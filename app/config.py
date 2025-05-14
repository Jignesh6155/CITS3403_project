class Config:
    SECRET_KEY = 'flask-login-key' # can also remove this and put it in a .env file
    SQLALCHEMY_DATABASE_URI = 'sqlite:///careerlink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add other default config options here

class DevelopmentConfig(Config):
    DEBUG = True
    # Add development-specific configs here

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific configs here

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # Add other testing-specific configs here