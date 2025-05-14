from flask import Flask
from app.models import db
# --- Flask-Login integration ---
from flask_login import LoginManager
from app.models import load_user
# --- Flask-WTF CSRF protection ---
from flask_wtf import CSRFProtect
import os

# Try to import Config from app.config, fallback to None if not present
try:
    from app.config import Config
except ImportError:
    Config = None

def create_app(config_object=None):
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)
    elif Config:
        app.config.from_object(Config)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///careerlink.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    db.init_app(app)
    # --- Flask-Login setup ---
    login = LoginManager()
    login.init_app(app)
    # Set the login view to the endpoint name for your login route
    # If your login route is @main_bp.route('/signin'), use 'main.signin'
    login.login_view = 'main.signin'
    # Register the user_loader functions
    login.user_loader(load_user)
    # --- Flask-WTF CSRF setup ---
    csrf = CSRFProtect(app)  # This enables CSRF protection for all forms
    # Import and register blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    return app