import pymongo
from cryptography.fernet import Fernet
from pymongo import MongoClient


class DatabaseManager:
    DATABASE_NAME = "SynePointsDb"

    def __init__(self, database_uri, secret_key, use_test_data=False):
        self.client = MongoClient(host=database_uri)
        self.db = self.client[self.DATABASE_NAME]
        self.fernet = Fernet(secret_key)
        if use_test_data:
            self._fill_db_with_test_data()

    def __del__(self):
        self.client.close()

    def store_user(self, user):
        return self.db.users.insert_one(user)

    def get_user(self, email):
        query = {'email': email}
        result = self.db.users.find_one(query)
        return result

    def get_all_users(self):
        result = self.db.users.find().sort([('points', pymongo.DESCENDING)])
        return result

    def store_prize(self, prize):
        return self.db.prizes.insert_one(prize)

    def get_all_prizes(self):
        return self.db.prizes.find()

    def store_jira_api_key(self, email, api_key):
        encrypted_key = self.fernet.encrypt(api_key.encode('UTF-8'))
        return self.db.users.update({'email': email}, {'$set': {'jira_api_key': encrypted_key}})

    def get_jira_api_key(self, email):
        user = self.get_user(email)
        if user:
            if 'jira_api_key' in user:
                encrypted_key = user['jira_api_key']
                return self.fernet.decrypt(encrypted_key)
            else:
                return None
        raise RuntimeError("User with email {} not found".format(email))

    def store_toggl_api_key(self, email, api_key):
        encrypted_key = self.fernet.encrypt(api_key.encode('UTF-8'))
        return self.db.users.update({'email': email}, {'$set': {'toggl_api_key': encrypted_key}})

    def get_toggl_api_key(self, email):
        user = self.get_user(email)
        if user:
            if 'toggl_api_key' in user:
                encrypted_key = user['toggl_api_key']
                return self.fernet.decrypt(encrypted_key)
            else:
                return None
        raise RuntimeError("User with email {} not found".format(email))

    def _fill_db_with_test_data(self):
        self._drop_db()

        self.store_user({'email': 'franta.pepa1@synetech.cz', 'points': 3})
        self.store_user({'email': 'franta.pepa3@synetech.cz', 'points': 5})
        self.store_user({'email': 'franta.pepa2@synetech.cz', 'points': 1})
        self.store_user({'email': 'marek.alexa@synetech.cz', 'points': 9999})

        self.store_prize({'name': 'Školení', 'price': 'dle domluvy'})
        self.store_prize({'name': 'Půjčení firemního drona na 3 dny', 'price': '50'})
        self.store_prize({'name': 'Půjčení firemního auta na 3 dny', 'price': '65'})
        self.store_prize({'name': 'Alza poukaz - 1000 Kč', 'price': '80'})
        self.store_prize({'name': 'Předplatné Spotify Premium na půl roku', 'price': '120'})
        self.store_prize({'name': 'Poukaz na gastronomický zážitek pro dva', 'price': '150'})
        self.store_prize({'name': 'Předplatné Netflix Standard na půl roku', 'price': '150'})
        self.store_prize({'name': 'Proplacení jízd Uberem do limitu 2000 Kč', 'price': '200'})
        self.store_prize({'name': 'Offroadový zážitek s Vráťou a jeho princeznou Ladou', 'price': '300'})
        self.store_prize({'name': 'Alza poukaz - 5000 Kč', 'price': '400'})
        self.store_prize({'name': 'Půjčení IPhone X či Android ekvivalent na rok', 'price': '1000'})

    def _drop_db(self):
        self.db.users.remove()
        self.db.prizes.remove()
