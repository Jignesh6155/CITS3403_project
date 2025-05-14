import unittest
from app import create_app
from app.models import db
from app.config import TestingConfig

class FlaskTestBase(unittest.TestCase):
    """
    Base class for Flask tests using an in-memory SQLite database.
    Inherit from this class in your test files for consistent setup/teardown.
    Uses TestingConfig for isolation.
    """
    def setUp(self):
        # Create app with testing config (in-memory DB)
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()    
        self.app_context.pop() 


# Example usage:
# from tests.base import FlaskTestBase
# class MyTest(FlaskTestBase):
#     def test_something(self):
#         ... 