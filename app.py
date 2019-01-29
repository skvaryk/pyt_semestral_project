import json
import os
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import make_google_blueprint, google
from jira import JIRA
from oauthlib.oauth2 import InvalidClientIdError

from DatabaseManager import DatabaseManager
from TogglWrapper import TogglWrapper, ProjectNotFoundException

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
        scope=["https://www.googleapis.com/auth/plus.me",
               "https://www.googleapis.com/auth/userinfo.email", ],
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
    if resp_json["hd"] != blueprint.authorization_url_params["hd"]:
        requests.post(
            "https://accounts.google.com/o/oauth2/revoke",
            params={"token": token["access_token"]}
        )
        session.clear()
        redirect('/')
    else:
        session['email'] = resp_json['email']


@app.route("/")
@login_required
def index():
    # if not session['email']:
    #     return redirect('/logout')
    resp_json = google.get("/oauth2/v2/userinfo").json()
    if not resp_json['email']:
        redirect('/logout')
    return "You are {email} on Google".format(email=session['email'])


@app.route('/users/', methods=['GET', 'POST'])
@login_required
def users():
    email = session['email']
    current_user = database_manager.get_user(email)
    all_users = database_manager.get_all_users()
    return render_template('pages/users.html', users=list(all_users), current_user=current_user)


@app.route('/prizes/', methods=['GET'])
@login_required
def prizes():
    email = session['email']
    user_points = database_manager.get_user(email)['points']
    prizes_list = list(database_manager.get_all_prizes())
    for prize in prizes_list:
        if str.isdigit(prize['price']) and int(prize['price']) > user_points:
            prize['requestable'] = False
    return render_template('pages/prizes.html', prizes=prizes_list, user_points=user_points)


@app.route('/prizes/<prize_id>/request/', methods=['POST'])
@login_required
def prizes_request(prize_id):
    email = session['email']
    user_points = database_manager.get_user(email)['points']
    prize = database_manager.get_prize(int(prize_id))
    if int(prize['price']) > user_points:
        return 'Sorry, it appears you do not have enough points for this prize.'
    database_manager.store_request(email, prize_id)
    flash('Prize requested.')
    return redirect(url_for('prizes'))


@app.route('/logout/')
def logout():
    # TODO: delete api tokens?
    token = google_bp.token["access_token"]
    google.post(
        "https://accounts.google.com/o/oauth2/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    session.clear()
    return "Logged out"


@app.route('/tasks/', methods=['GET'])
@login_required
def tasks():
    email = session['email']
    jira_api_key = database_manager.get_jira_api_key(email)
    if not jira_api_key:
        return redirect('/jira/register')

    options = {'server': 'https://synetech.atlassian.net'}
    jira_client = JIRA(options, basic_auth=(email, jira_api_key))
    # TODO: replace currentuser()
    jql = 'assignee=currentuser() AND status not in (resolved, closed) AND createdDate >= -365d'

    block_size = 100
    block_num = 0
    jira_tasks = []
    while True:
        start_idx = block_num * block_size
        issues = jira_client.search_issues(jql, start_idx, block_size)
        if len(issues) == 0:
            # Retrieve issues until there are no more to come
            break
        block_num += 1
        jira_tasks.extend(issues)

    for jira_task in jira_tasks:
        transitions = jira_client.transitions(jira_task.key)
        jira_task.transitions = transitions

    email = session['email']
    toggl_api_key = database_manager.get_toggl_api_key(email)
    current_task_key = ""
    if toggl_api_key:
        toggl_wrapper = TogglWrapper(toggl_api_key, "SynePoints", 689492)
        current_time_entry = toggl_wrapper.get_current_time_entry()
        if current_time_entry and current_time_entry['tid']:
            current_task = toggl_wrapper.get_task(current_time_entry['tid'], current_time_entry['pid'])
            current_task_key = current_task['name'].split(' ')[0]

    return render_template('pages/tasks.html', tasks=jira_tasks, current_task_key=current_task_key)


@app.route('/jira/register/', methods=['GET', 'POST'])
@login_required
def jira_register():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Login':
            email = session['email']
            jira_api_key = request.form['api_key']
            database_manager.store_jira_api_key(email, jira_api_key)
            return redirect("/tasks")
    return render_template('pages/jira_register.html')


@app.route('/toggl/register/', methods=['GET', 'POST'])
@login_required
def toggl_register():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Login':
            email = session['email']
            jira_api_key = request.form['api_key']
            database_manager.store_toggl_api_key(email, jira_api_key)
            return redirect("/tasks")
    return render_template('pages/toggl_register.html')


@app.route('/tasks/<task_key>/stop/', methods=['POST'])
@login_required
def tasks_stop_timer(task_key):
    email = session['email']
    api_key = database_manager.get_toggl_api_key(email)
    if not api_key:
        return redirect('/toggl/register')
    toggl_wrapper = TogglWrapper(api_key, "SynePoints", 689492)
    toggl_wrapper.stop_time_entry(task_key)
    return redirect("/tasks")


@app.route('/tasks/<task_key>/start/', methods=['POST'])
@login_required
def tasks_start_timer(task_key):
    email = session['email']
    api_key = database_manager.get_toggl_api_key(email)
    if not api_key:
        return redirect('/toggl/register')
    toggl_wrapper = TogglWrapper(api_key, "SynePoints", 689492)
    try:
        toggl_wrapper.start_time_entry(task_key)
    except ProjectNotFoundException as e:
        return e.message
    return redirect("/tasks")


@app.route('/tasks/<task_key>/comment/', methods=['POST'])
@login_required
def tasks_comment(task_key):
    text = request.form['text']
    email = session['email']
    jira_api_key = database_manager.get_jira_api_key(email)
    if not jira_api_key:
        return redirect('/jira/register')
    options = {'server': 'https://synetech.atlassian.net'}
    jira_client = JIRA(options, basic_auth=(email, jira_api_key))
    jira_client.add_comment(task_key, text)
    return redirect("/tasks")


@app.route('/tasks/<task_key>/transition/<transition_id>/', methods=['POST'])
@login_required
def tasks_transition(task_key, transition_id):
    email = session['email']
    jira_api_key = database_manager.get_jira_api_key(email)
    if not jira_api_key:
        return redirect('/jira/register')
    options = {'server': 'https://synetech.atlassian.net'}
    jira_client = JIRA(options, basic_auth=(email, jira_api_key))
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
    return redirect("/users")


@app.route('/requests/', methods=['GET'])
@login_required
def requests():
    email = session['email']
    user_requests = list(database_manager.get_requests(email))
    for user_request in user_requests:
        prize = database_manager.get_prize(user_request['prize_id'])
        user_request['description'] = prize['description']
        user_request['price'] = prize['price']
        user_request['date'] = user_request['_id'].generation_time

    return render_template('pages/requests.html', requests=user_requests)


@app.errorhandler(InvalidClientIdError)
def handle_error(e):
    print(e.message)
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run()
