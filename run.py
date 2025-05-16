import os
from app import create_app
from app.models import db
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

# Change this to the appropriate config for the environment you're running in
# Choose from DevelopmentConfig, ProductionConfig, or TestingConfig
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
config_name = os.environ.get("APP_CONFIG", "development")
app = create_app(config_map[config_name])

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(port=5001)