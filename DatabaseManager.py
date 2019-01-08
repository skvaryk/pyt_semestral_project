from pymongo import MongoClient


# from random import randint
#
# # Step 1: Connect to MongoDB - Note: Change connection string as needed
# client = MongoClient(port=27017)
# db = client.business
# # Step 2: Create sample data
# names = ['Kitchen', 'Animal', 'State', 'Tastey', 'Big', 'City', 'Fish', 'Pizza', 'Goat', 'Salty', 'Sandwich', 'Lazy',
#          'Fun']
# company_type = ['LLC', 'Inc', 'Company', 'Corporation']
# company_cuisine = ['Pizza', 'Bar Food', 'Fast Food', 'Italian', 'Mexican', 'American', 'Sushi Bar', 'Vegetarian']
# for x in range(1, 501):
#     business = {
#         'name': names[randint(0, (len(names) - 1))] + ' ' + names[randint(0, (len(names) - 1))] + ' ' + company_type[
#             randint(0, (len(company_type) - 1))],
#         'rating': randint(1, 5),
#         'cuisine': company_cuisine[randint(0, (len(company_cuisine) - 1))]
#     }
#     # Step 3: Insert business object directly into MongoDB via insert_one
#     result = db.reviews.insert_one(business)
#     # Step 4: Print to the console the ObjectID of the new document
#     print('Created {0} of 100 as {1}'.format(x, result.inserted_id))
# # Step 5: Tell us that you are done
# print('finished creating 100 business reviews')
#

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
        print(result.inserted_id)
        return result

    def get_user(self, user_id):
        query = {'_id': user_id}
        result = self.db.users.find(query)
        return result

    def get_all_users(self):
        result = self.db.users.find()
        return result
