import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    MONGO_USER = os.environ['MONGO_USER']
    MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
    MONGO_DATABASE_URI = "mongodb+srv://{}:{}@synepoints-f8xsm.mongodb.net/test".format(MONGO_USER, MONGO_PASSWORD)


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    # don't require https - only for local testing
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
