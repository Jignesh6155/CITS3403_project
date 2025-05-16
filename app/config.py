import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Note Headless Toggle refers to the use of a headless browser for scraping.

# Base configuration with default settings.
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///careerlink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HEADLESS_TOGGLE = True  # Default to True for safety
    
# Development configuration with debug and fallback secret key.
class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-Temporary_Key')
    HEADLESS_TOGGLE = False

# Production configuration with environment variable for secret key.
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    HEADLESS_TOGGLE = True

# Testing configuration using in-memory database and disabled CSRF.
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-Temporary_Key')
    WTF_CSRF_ENABLED = False
    HEADLESS_TOGGLE = False