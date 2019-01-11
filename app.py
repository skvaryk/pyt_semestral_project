import json
import os
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import make_google_blueprint, google
from jira import JIRA

from DatabaseManager import DatabaseManager

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

database_manager = DatabaseManager(app.config['MONGO_DATABASE_URI'], app.config['SECRET_KEY'], use_test_data=True)

# don't require https - only for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

with open('client_id.json') as file:
    client_id = json.load(file)
    web = client_id['web']

    google_bp = make_google_blueprint(
        client_id=web['client_id'],
        client_secret=web['client_secret'],
        scope=["https://www.googleapis.com/auth/plus.me",
               "https://www.googleapis.com/auth/userinfo.email", ],
        hosted_domain="synetech.cz"
    )

    app.register_blueprint(google_bp, url_prefix="/login")


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


@app.route("/")
@login_required
def index():
    resp_json = google.get("/oauth2/v2/userinfo").json()
    if not resp_json['email']:
        redirect('/logout')
    session['email'] = resp_json['email']
    return "You are {email} on Google".format(email=resp_json['email'])


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'POST':
        if request.form['submit_button'] == 'add_user':
            print(request.form['email'])
            user = {
                'email': request.form['email'],
                'points': request.form['points']
            }
            database_manager.store_user(user)

    return render_template('pages/users.html',
                           users=list(database_manager.get_all_users()))


@app.route('/prizes')
@login_required
def prizes():
    return render_template('pages/prizes.html',
                           prizes=list(database_manager.get_all_prizes()))


@app.route('/logout')
def logout():
    token = google_bp.token["access_token"]
    google.post(
        "https://accounts.google.com/o/oauth2/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    session.clear()
    return "Logged out"


@app.route('/jira', methods=['GET', 'POST'])
@login_required
def jira():
    email = session['email']
    jira_api_key = database_manager.get_jira_api_key(email)
    if not jira_api_key:
        return redirect('/jira/register')

    # By default, the client will connect to a JIRA instance started from the Atlassian Plugin SDK
    # (see https://developer.atlassian.com/display/DOCS/Installing+the+Atlassian+Plugin+SDK for details).
    # Override this with the options parameter.
    options = {
        'server': 'https://synetech.atlassian.net'
    }

    jira_client = JIRA(options, basic_auth=(email, jira_api_key))

    # Get all projects viewable by anonymous users.
    projects = jira_client.projects()

    # Sort available project keys, then return the second, third, and fourth keys.
    keys = sorted([project.key for project in projects])
    print(keys)

    # TODO: replace currentuser()
    jql = 'assignee=currentuser() AND status not in (resolved, closed) AND createdDate >= -365d'

    block_size = 100
    block_num = 0
    tasks = []
    while True:
        start_idx = block_num * block_size
        issues = jira_client.search_issues(jql, start_idx, block_size)
        if len(issues) == 0:
            # Retrieve issues until there are no more to come
            break
        block_num += 1
        for issue in issues:
            tasks.append(issue.key)

    return str(tasks)


@app.route('/jira/register', methods=['GET', 'POST'])
@login_required
def jira_register():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Login':
            email = session['email']
            jira_api_key = request.form['api_key']
            database_manager.store_jira_api_key(email, jira_api_key)
            return redirect("/jira")
    return render_template('pages/jira_register.html')


if __name__ == '__main__':
    app.run()
