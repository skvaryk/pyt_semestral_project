import json
import os
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import make_google_blueprint, google

from DatabaseManager import DatabaseManager

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

database_manager = DatabaseManager(app.config["MONGO_DATABASE_URI"], use_test_data=True)

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
        os.abort(403)


@app.route("/login/google/authorized")
def authorized():
    print("authorized")


@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    return "You are {email} on Google".format(email=resp.json()["email"])


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

    # elif request.method == 'GET':
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
    # abort(403)
    return "Logged out"


if __name__ == '__main__':
    app.run()
