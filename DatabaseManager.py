from sqlite3.dbapi2 import Date

import pymongo
from bson import ObjectId
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

    def _store_user(self, user):
        return self.db.users.insert_one(user)

    def get_user(self, email):
        query = {'email': email}
        return self.db.users.find_one(query)

    def get_all_users(self):
        return self.db.users.find().sort([('points', pymongo.DESCENDING)])

    def store_prize(self, prize):
        return self.db.prizes.insert_one(prize)

    def get_all_prizes(self):
        return self.db.prizes.find()

    def store_jira_api_token(self, email, api_token):
        encrypted_token = self.fernet.encrypt(api_token.encode('UTF-8'))
        return self.db.users.update({'email': email}, {'$set': {'jira_api_token': encrypted_token}})

    def get_jira_api_token(self, email):
        user = self.get_user(email)
        if user:
            if 'jira_api_token' in user:
                encrypted_token = user['jira_api_token']
                return self.fernet.decrypt(encrypted_token)
            else:
                return None
        raise RuntimeError("User with email {} not found".format(email))

    def store_toggl_api_token(self, email, api_token):
        encrypted_token = self.fernet.encrypt(api_token.encode('UTF-8'))
        return self.db.users.update({'email': email}, {'$set': {'toggl_api_token': encrypted_token}})

    def get_toggl_api_token(self, email):
        user = self.get_user(email)
        if user:
            if 'toggl_api_token' in user:
                encrypted_token = user['toggl_api_token']
                return self.fernet.decrypt(encrypted_token)
            else:
                return None
        raise RuntimeError("User with email {} not found".format(email))

    def _fill_db_with_test_data(self):
        self._drop_db()

        self._store_user(
            {'email': 'daniel.rutkovsky@synetech.cz', 'fullname': 'Daniel Rutkovský', 'role': 'user', 'points': 3,
             'team': []})
        self._store_user(
            {'email': 'miroslav.voda@synetech.cz', 'fullname': 'Miroslav Voda', 'role': 'user', 'points': 5,
             'team': [1]})
        self._store_user(
            {'email': 'vratislav.zima@synetech.cz', 'fullname': 'Vratislav Zima', 'role': 'admin', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'eduard.fuzessery@synetech.cz', 'fullname': 'Eduard Fuzessery', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'jana.ernekerova@synetech.cz', 'fullname': 'Jana Ernekerová', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'samuel.bily@synetech.cz', 'fullname': 'Samuel Bilý', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'lubomir.baloun@synetech.cz', 'fullname': 'Lubomír Baloun', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'lukas.vsetecka@synetech.cz', 'fullname': 'Lukáš Všetečka', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'jiri.novacek@synetech.cz', 'fullname': 'Jiří Nováček', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'marek.alexa@synetech.cz', 'fullname': 'Marek Alexa', 'role': 'admin', 'points': 100,
             'team': [1, 2]})
        self._store_user(
            {'email': 'stepan.kloucek@synetech.cz', 'fullname': 'Štěpán Klouček', 'role': 'user', 'points': 1,
             'team': [2]})
        self._store_user(
            {'email': 'jiri.rychlovsky@synetech.cz', 'fullname': 'Jiří Rychlovský', 'role': 'user', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'vojtech.drbohlav@synetech.cz', 'fullname': 'Vojtěch Drbohlav', 'role': 'user', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'eva.meclova@synetech.cz', 'fullname': 'Eva Mečlová', 'role': 'admin', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'vojtech.pajer@synetech.cz', 'fullname': 'Vojtech Pajer', 'role': 'user', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'lukas.ruzicka@synetech.cz', 'fullname': 'Lukáš Růžička', 'role': 'user', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'tadeas.musil@synetech.cz', 'fullname': 'Tadeáš Musil', 'role': 'user', 'points': 1,
             'team': [2]})

        self._store_user(
            {'email': 'tomas.novotny@synetech.cz', 'fullname': 'Tomáš Novotný', 'role': 'user', 'points': 1,
             'team': [2]})

        self.store_prize({'id': 0, 'requestable': False, 'description': 'Školení', 'price': 'dle domluvy'})
        self.store_prize(
            {'id': 1, 'requestable': True, 'description': 'Půjčení firemního drona na 3 dny', 'price': '50'})
        self.store_prize(
            {'id': 2, 'requestable': True, 'description': 'Půjčení firemního auta na 3 dny', 'price': '65'})
        self.store_prize({'id': 3, 'requestable': True, 'description': 'Alza poukaz - 1000 Kč', 'price': '80'})
        self.store_prize(
            {'id': 4, 'requestable': True, 'description': 'Předplatné Spotify Premium na půl roku', 'price': '120'})
        self.store_prize(
            {'id': 5, 'requestable': True, 'description': 'Poukaz na gastronomický zážitek pro dva', 'price': '150'})
        self.store_prize(
            {'id': 6, 'requestable': True, 'description': 'Předplatné Netflix Standard na půl roku', 'price': '150'})
        self.store_prize(
            {'id': 7, 'requestable': True, 'description': 'Proplacení jízd Uberem do limitu 2000 Kč', 'price': '200'})
        self.store_prize(
            {'id': 8, 'requestable': True, 'description': 'Offroadový zážitek s Vráťou a jeho princeznou Ladou',
             'price': '300'})
        self.store_prize({'id': 9, 'requestable': True, 'description': 'Alza poukaz - 5000 Kč', 'price': '400'})
        self.store_prize(
            {'id': 10, 'requestable': True, 'description': 'Půjčení IPhone X či Android ekvivalent na rok',
             'price': '1000'})

        reward_category_project = {'name': 'PROJEKT', 'rewards': [
            {'description': 'Dohození projektu pro firmu - po podepsání smlouvy', 'points': '150'},
            {'description': 'Dokončená aplikace - aplikace po akceptaci, uzavřená finální faktura', 'points': '100'},
            {'description': 'Uzavřená měsíční faktura - SLA / milník - vyfakturováno klientovi - (více než 5MD)',
             'points': '20'},
            {'description': 'Úspěšná release / stage verze - předána klientovi a ten je spokojen', 'points': '15'},
            {'description': 'Nalezený kritcký bug při testování stage / release verze', 'points': '10'},
        ]}
        reward_category_diligence = {'name': 'PRACOVITOST', 'rewards': [
            {'description': 'Počet odpracovaných hodin za měsíc - více než 110 / 120 / 140', 'points': '5 / 10 /20'},
            {'description': '100% týdenní účast na standupu projektu', 'points': 'su / týden'},
            {'description': 'Odměna reviewerem za čistý PR (max 20 za měsíc)', 'points': '5'},
            {'description': 'Docházka - příchod do 8:45', 'points': '1'},
            {'description': 'Dohození projektu pro firmu - po podepsání smlouvy', 'points': 150},

        ]}
        reward_category_branding = {'name': 'BRANDING', 'rewards': [
            {'description': 'Prezentace firmy na externí akci', 'points': '50'},
            {'description': 'Příspěvek na blog', 'points': '30 - 50'},
            {'description': 'Připravený vlastní content pro soc sítě / web', 'points': '10'},
            {'description': 'Sdílení firemních postů na svém účtu', 'points': '1'},
            {'description': 'Výroba / návrh materiálů pro propagaci firmy - reálně použito pro marketing',
             'points': 'dle Evičky'},

        ]}
        reward_category_company = {'name': 'FIRMA', 'rewards': [
            {'description': 'Zorganizování firemní akce', 'points': '20'},
            {'description': 'Prezentující libovolného tématu pro zbytek firmy (mimo prezentace projektů)',
             'points': '10'},
            {'description': 'Věcný příspěvek pro dobro firmy', 'points': '5'},
            {'description': 'Nejlepší prezentace projektu', 'points': '5'},
        ]}
        reward_category_misc = {'name': 'MISCELLANEOUS', 'rewards': [
            {'description': 'navrhuje kdokoliv komukoliv - akceptuje vedení SYNEGAMES', 'points': 'neomezeně'},
        ]}
        self.db.rewards.insert_many(
            [reward_category_project, reward_category_diligence, reward_category_branding,
             reward_category_company, reward_category_misc])

        team_oriflame = {'id': 1, 'name': 'Oriflame'}
        team_fiddo = {'id': 2, 'name': 'Fiddo'}
        self.db.teams.insert_many([team_oriflame, team_fiddo])

    def _drop_db(self):
        self.db.teams.remove()
        print(list(self.get_teams()))
        self.db.users.remove()
        print(list(self.get_all_users()))
        self.db.prizes.remove()
        print(list(self.get_all_prizes()))
        self.db.requests.remove()
        print(list(self.get_ungranted_requests()))
        self.db.rewards.remove()
        print(list(self.get_all_rewards()))
        import time
        time.sleep(5)

    def assign_points(self, user_email, points, reason, changed_by):
        self.store_record({'change_by': changed_by, 'user': user_email, 'reason': reason, 'points': points})
        self.update_points(user_email, points)

    def update_points(self, user_email, points):
        self.db.users.update({'email': user_email}, {'$inc': {'points': points}})

    def store_record(self, record):
        return self.db.records.insert_one(record)

    def get_prize(self, prize_id):
        query = {'id': int(prize_id)}
        return self.db.prizes.find_one(query)

    def store_request(self, email, prize_id):
        prize = self.get_prize(prize_id)
        self.update_points(email, -int(prize['price']))
        request = {'email': email, 'prize_id': prize_id, 'granted': False}
        return self.db.requests.insert_one(request)

    def get_ungranted_requests(self):
        query = {'granted': False}
        return self.db.requests.find(query)

    def get_requests(self, email):
        query = {'email': email}
        return self.db.requests.find(query)

    def cancel_request(self, request_id):
        request = self.get_request(request_id)
        prize = self.get_prize(request['prize_id'])
        self.update_points(request['email'], int(prize['price']))
        query = {'_id': ObjectId(request_id)}
        return self.db.requests.delete_one(query)

    def store_rewards_category(self, category):
        return self.db.rewards.insert_one(category)

    def get_all_rewards(self):
        return self.db.rewards.find()

    def grant_request(self, request_id, granted_by):
        request = self.get_request(request_id)
        prize = self.get_prize(request['prize_id'])
        self.store_record(
            {'change_by': granted_by, 'user': request['email'], 'request_id': request['_id'],
             'points': -int(prize['price'])})
        return self.db.requests.update({'_id': request['_id']}, {'$set': {'granted': True}})

    def get_request(self, request_id):
        query = {'_id': ObjectId(request_id)}
        return self.db.requests.find_one(query)

    def query_users(self, name, team_id=-1):
        if not name:
            name = ''

        if team_id == -1:
            query = {'email': {'$regex': name}}
        else:
            query = {'email': {'$regex': name}, 'team': team_id}
        return self.db.users.find(query)

    def get_teams(self):
        return self.db.teams.find()
