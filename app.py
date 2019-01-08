import os

from flask import Flask, render_template, request

from DatabaseManager import DatabaseManager

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

database_manager = DatabaseManager(app.config["MONGO_DATABASE_URI"], app.config["MONGO_DATABASE_PORT"],
                                   use_test_data=True)


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/users', methods=['GET', 'POST'])
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
    return render_template('users.html', my_string="Hello", my_list=list(database_manager.get_all_users()))


if __name__ == '__main__':
    app.run()
