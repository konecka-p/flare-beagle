import os

class Config(object):
    DEBUG = False

    CSRF_ENABLED = True
    # SECRET_KEY = 'YOUR_RANDOM_SECRET_KEY'
    SECRET_KEY = os.environ.get('SECRET>_KEY') or "my_secret_key"

    MONGODB_DB = 'flare_beagleDB'
    MONGODB_HOST = '0.0.0.0'
    MONGODB_PORT = 27017
    ENV = 'development'
    # SERVER_NAME = '0.0.0.0:5000'
    SERVER_NAME = 'localhost:5000'
    MONGO_URI = "mongodb://localhost:27017/flare_beagleDB"


class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True