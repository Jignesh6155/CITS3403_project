from flask import Flask
from app.models import db

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
        app.secret_key = "your_secret_key"
    db.init_app(app)
    # Import and register blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    return app