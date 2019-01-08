import os
from flask import Flask, render_template
from DatabaseManager import DatabaseManager

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

database_manager = DatabaseManager(app.config["MONGO_DATABASE_URI"], app.config["MONGO_DATABASE_PORT"],
                                   use_test_data=True)


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/users')
def users():
    # return "Hello {}!".format("bla")
    print(database_manager.get_all_users())
    return render_template('users.html', my_string="Wheeeee!", my_list=list(database_manager.get_all_users()))
    # return "Hello {}!".format(list(database_manager.get_all_users()))


if __name__ == '__main__':
    app.run()
