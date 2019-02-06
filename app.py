import json
import os
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import make_google_blueprint, google
from jira import JIRA
from oauthlib.oauth2 import InvalidClientIdError, InvalidGrantError

from DatabaseManager import DatabaseManager
from JiraWrapper import JiraWrapper
from TogglWrapper import TogglWrapper, ProjectNotFoundException

SYNETECH_WORKSPACE_ID = 689492

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
Bootstrap(app)

database_manager = DatabaseManager(app.config['MONGO_DATABASE_URI'], app.config['SECRET_KEY'],
                                   use_test_data=False)

with open('client_id.json') as file:
    client_id = json.load(file)
    web = client_id['web']

    google_bp = make_google_blueprint(
        client_id=web['client_id'],
        client_secret=web['client_secret'],
        scope=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        hosted_domain="synetech.cz",
        offline=True,
    )

    app.register_blueprint(google_bp, url_prefix="/login")


@app.errorhandler(ValueError)
def handle_bad_request(e):
    return 'bad request! {}'.format(str(e)), 400


app.register_error_handler(400, handle_bad_request)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not google.authorized:
            return redirect(url_for('google.login'))
        return f(*args, **kwargs)

    return decorated_function


@oauth_authorized.connect_via(google_bp)
def logged_in(blueprint, token):
    resp_json = google.get("/oauth2/v2/userinfo").json()
    user = database_manager.get_user(resp_json['email'])
    if not user:
        return 'User entry not found. Please contact the administrator to get registered.'

    # check if email is from hosted_domain
    if resp_json["hd"] != blueprint.authorization_url_params["hd"]:
        requests.post(
            "https://accounts.google.com/o/oauth2/revoke",
            params={"token": token["access_token"]}
        )
        session.clear()
        redirect('/')
    else:
        session['current_user_email'] = user['email']
        session['current_user_role'] = user['role']
        session['current_user_points'] = user['points']


@app.route("/")
@login_required
def index():
    return redirect('/overview')


@app.route('/overview/', methods=['GET'])
@login_required
def overview():
    all_users = database_manager.get_all_users()
    return render_template('pages/overview.html', users=list(all_users))


@app.route('/rewards/', methods=['GET', 'POST'])
@login_required
def rewards():
    reward_categories = database_manager.get_all_rewards()
    return render_template('pages/rewards.html', reward_categories=list(reward_categories))


@app.route('/prizes/', methods=['GET'])
@login_required
def prizes():
    prizes_list = list(database_manager.get_all_prizes())
    return render_template('pages/prizes.html', prizes=prizes_list)


@app.route('/prizes/<prize_id>/request/', methods=['POST'])
@login_required
def prizes_request(prize_id):
    email = session['current_user_email']
    user_points = database_manager.get_user(email)['points']
    prize = database_manager.get_prize(int(prize_id))
    price = int(prize['price'])
    if int(prize['price']) > user_points:
        return 'Sorry, it appears you do not have enough points for this prize.'
    notify_by_mail(email, prize)
    database_manager.store_request(email, prize_id)
    session['current_user_points'] -= price
    flash('Prize requested.')
    return redirect(url_for('prizes'))


def notify_by_mail(user_mail, prize):
    if 'DEBUG' in app.config and app.config['DEBUG']:
        server_url = 'http://localhost:5000/awesome-email/us-central1/sendEmail'
    else:
        server_url = 'https://europe-west1-awesome-email.cloudfunctions.net/sendEmail/'
    message = '{} has requested the \'{}\' prize.'.format(user_mail, prize['description'])
    data_dict = {'name': user_mail, 'subject': 'SynePoints - Prize request', 'email': user_mail, 'message': message}
    data = json.dumps(data_dict)
    headers = {"Content-Type": "application/json"}
    response = requests.post(server_url, data=data, headers=headers)
    print(response.status_code)


@app.route('/logout/')
def logout():
    token = google_bp.token["access_token"]
    google.post(
        "https://accounts.google.com/o/oauth2/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    del google_bp.token
    session.clear()
    return "Logged out"


@app.route('/tasks/', methods=['GET'])
@login_required
def tasks():
    email = session['current_user_email']
    jira_api_token = database_manager.get_jira_api_token(email)
    if not jira_api_token:
        return redirect('/jira/register')

    jira_client = JiraWrapper(server='https://synetech.atlassian.net', basic_auth=(email, jira_api_token))
    jira_tasks = jira_client.get_tasks_with_transitions()

    toggl_api_token = database_manager.get_toggl_api_token(email)
    current_task_key = ""
    if toggl_api_token:
        toggl_wrapper = TogglWrapper(toggl_api_token, "SynePoints", SYNETECH_WORKSPACE_ID)
        current_task_key = toggl_wrapper.get_current_task_key()

    return render_template('pages/tasks.html', tasks=jira_tasks, current_task_key=current_task_key)


@app.route('/jira/register/', methods=['GET', 'POST'])
@login_required
def jira_register():
    if request.method == 'POST':
        if request.form.get('submit_button') == 'Login':
            email = session['current_user_email']
            jira_api_token = request.form.get('api_token')
            database_manager.store_jira_api_token(email, jira_api_token)
            return redirect("/tasks")
    return render_template('pages/jira_register.html')


@app.route('/toggl/register/', methods=['GET', 'POST'])
@login_required
def toggl_register():
    if request.method == 'POST':
        if request.form.get('submit_button') == 'Login':
            email = session['current_user_email']
            jira_api_token = request.form.get('api_token')
            database_manager.store_toggl_api_token(email, jira_api_token)
            return redirect("/tasks")
    return render_template('pages/toggl_register.html')


@app.route('/tasks/<task_key>/stop/', methods=['POST'])
@login_required
def tasks_stop_timer(task_key):
    email = session['current_user_email']
    toggl_api_token = database_manager.get_toggl_api_token(email)
    if not toggl_api_token:
        return redirect('/toggl/register')
    toggl_wrapper = TogglWrapper(toggl_api_token, "SynePoints", SYNETECH_WORKSPACE_ID)
    toggl_wrapper.stop_time_entry(task_key)
    return redirect("/tasks")


@app.route('/tasks/<task_key>/start/', methods=['POST'])
@login_required
def tasks_start_timer(task_key):
    email = session['current_user_email']
    toggl_api_token = database_manager.get_toggl_api_token(email)
    if not toggl_api_token:
        return redirect('/toggl/register')
    toggl_wrapper = TogglWrapper(toggl_api_token, "SynePoints", SYNETECH_WORKSPACE_ID)
    try:
        toggl_wrapper.start_time_entry(task_key)
    except ProjectNotFoundException as e:
        return e.message
    return redirect("/tasks")


@app.route('/tasks/<task_key>/comment/', methods=['POST'])
@login_required
def tasks_comment(task_key):
    text = request.form['text']
    email = session['current_user_email']
    jira_api_token = database_manager.get_jira_api_token(email)
    if not jira_api_token:
        return redirect('/jira/register')
    options = {'server': 'https://synetech.atlassian.net'}
    jira_client = JIRA(options, basic_auth=(email, jira_api_token))
    jira_client.add_comment(task_key, text)
    return redirect("/tasks")


@app.route('/tasks/<task_key>/transition/<transition_id>/', methods=['POST'])
@login_required
def tasks_transition(task_key, transition_id):
    email = session['current_user_email']
    jira_api_token = database_manager.get_jira_api_token(email)
    if not jira_api_token:
        return redirect('/jira/register')
    options = {'server': 'https://synetech.atlassian.net'}
    jira_client = JIRA(options, basic_auth=(email, jira_api_token))
    jira_client.transition_issue(task_key, transition_id)
    return redirect("/tasks")


@app.route('/users/<assignee_email>/points/', methods=['POST'])
@login_required
def users_assign_points(assignee_email):
    points = int(request.form['points'])
    reason = request.form['reason']

    resp_json = google.get('/oauth2/v2/userinfo').json()
    if not resp_json['email']:
        redirect('/logout')
    current_user_email = resp_json['email']
    user = database_manager.get_user(current_user_email)
    if 'role' in user and (user['role'] == 'admin' or user['role'] == 'pm'):
        database_manager.assign_points(assignee_email, points, reason, current_user_email)
    else:
        return 'Not authorized'
    return redirect("/overview")


@app.route('/requests/', methods=['GET'])
@login_required
def requests_list():
    email = session['current_user_email']
    user_requests = list(database_manager.get_requests(email))
    for user_request in user_requests:
        prize = database_manager.get_prize(user_request['prize_id'])
        user_request['description'] = prize['description']
        user_request['price'] = prize['price']
        user_request['date'] = user_request['_id'].generation_time

    ungranted_requests = None
    current_user = database_manager.get_user(email)
    if 'role' in current_user and current_user['role'] == 'admin':
        ungranted_requests = list(database_manager.get_ungranted_requests())
        for ungranted_request in ungranted_requests:
            prize = database_manager.get_prize(ungranted_request['prize_id'])
            ungranted_request['description'] = prize['description']
            ungranted_request['date'] = ungranted_request['_id'].generation_time

    return render_template('pages/requests.html', requests=user_requests,
                           ungranted_requests=ungranted_requests)


@app.route('/requests/<request_id>/cancel/', methods=['POST'])
@login_required
def requests_cancel(request_id):
    database_manager.cancel_request(request_id)
    user = database_manager.get_user(session.get('current_user_email'))
    session['current_user_points'] = user['points']
    return redirect("/requests")


@app.route('/requests/<request_id>/grant/', methods=['POST'])
@login_required
def requests_grant(request_id):
    resp_json = google.get('/oauth2/v2/userinfo').json()
    if not resp_json['email']:
        redirect('/logout')
    current_user_email = resp_json['email']
    current_user = database_manager.get_user(current_user_email)
    if 'role' in current_user and current_user['role'] == 'admin':
        database_manager.grant_request(request_id, current_user_email)
    return redirect("/requests")


@app.route('/assign_points/', methods=['GET', 'POST'])
@login_required
def assign_points():
    include_users = request.form.getlist('include_checkbox')
    points = request.form.get('points')
    if include_users and str.isdigit(points):
        reason = request.form.get('reason')
        points_int = int(points)

        resp_json = google.get('/oauth2/v2/userinfo').json()
        if not resp_json['email']:
            redirect('/logout')
        current_user_email = resp_json['email']
        current_user = database_manager.get_user(current_user_email)
        if 'role' in current_user and (current_user['role'] == 'admin' or current_user['role'] == 'pm'):
            for user_email in include_users:
                database_manager.assign_points(user_email, points_int, reason, current_user_email)
                session['current_user_points'] += points_int
        else:
            return 'Not authorized'
        flash('Points assigned.')

    teams = list(database_manager.get_teams())
    users = database_manager.get_all_users()
    return render_template('pages/assign_points.html', teams=list(teams),
                           users=list(users))


@app.route('/assign_points/query/', methods=['POST'])
@login_required
def assign_points_query():
    team_id = request.form.get('select')
    name_contains = request.form.get('menu_text')
    if not name_contains:
        name_contains = request.form.get('top_text')

    if team_id is not None:
        filtered_users = database_manager.query_users(name_contains, int(team_id))
    else:  # No team selected
        filtered_users = database_manager.query_users(name_contains)

    teams = list(database_manager.get_teams())
    return render_template('pages/assign_points.html', teams=list(teams),
                           users=list(filtered_users))


@app.errorhandler(InvalidClientIdError)
def handle_error(e):
    session.clear()
    return redirect(url_for('google.login'))


@app.errorhandler(InvalidGrantError)
def handle_grant_error(e):
    session.clear()
    return redirect(url_for('google.login'))


if __name__ == '__main__':
    app.run()
