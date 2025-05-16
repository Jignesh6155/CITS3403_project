import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///careerlink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-Temporary_Key')
    SECRET_KEY = "Temporary_Key"

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-Temporary_Key')
    WTF_CSRF_ENABLED = False