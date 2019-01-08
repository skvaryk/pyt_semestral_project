from pymongo import MongoClient


class DatabaseManager:
    DATABASE_NAME = "SynePointsDb"

    def __init__(self, database_uri, database_port, use_test_data=False):
        self.client = MongoClient(host=database_uri, port=database_port)
        self.db = self.client[self.DATABASE_NAME]
        if use_test_data:
            self.fill_db_with_test_data()

    def fill_db_with_test_data(self):
        self.client.drop_database(self.DATABASE_NAME)
        self.db = self.client[self.DATABASE_NAME]
        user1 = {'email': 'franta.pepa1@synetech.cz', 'points': 3}
        user2 = {'email': 'franta.pepa2@synetech.cz', 'points': 4}
        user3 = {'email': 'franta.pepa3@synetech.cz', 'points': 5}
        self.store_user(user1)
        self.store_user(user2)
        self.store_user(user3)

    def __del__(self):
        self.client.close()

    def store_user(self, user):
        result = self.db.users.insert_one(user)
        return result

    def get_user(self, user_id):
        query = {'_id': user_id}
        result = self.db.users.find(query)
        return result

    def get_all_users(self):
        result = self.db.users.find()
        return result
