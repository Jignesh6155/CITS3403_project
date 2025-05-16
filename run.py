from app import create_app
from app.models import db
from app.config import DevelopmentConfig
from app.config import ProductionConfig
from app.config import TestingConfig

# Change this to the appropriate config for the environment you're running in
# Choose from DevelopmentConfig, ProductionConfig, or TestingConfig
app = create_app(DevelopmentConfig)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5001)