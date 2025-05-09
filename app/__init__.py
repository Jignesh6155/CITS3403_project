from flask import Flask
from app.models import db
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///careerlink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key"

csrf = CSRFProtect(app)

db.init_app(app)

from app import routes