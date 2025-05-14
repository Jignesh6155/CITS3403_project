from flask import Flask
from app.models import db

def create_app(config_object=None):
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///careerlink.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.secret_key = "your_secret_key"
    db.init_app(app)
    # Import and register blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    return app