"""
Base testing utilities for Flask application tests.

This module provides a foundational test class that sets up an in-memory SQLite database
for Flask application testing, ensuring each test runs in isolation. It handles
test database creation, teardown, and provides utilities like force_login for authentication.
"""
import unittest
from app import create_app
from app.models import db
from app.config import TestingConfig

class FlaskTestBase(unittest.TestCase):
    """
    Base class for Flask tests using an in-memory SQLite database.
    
    This class provides common setup and teardown operations for all test cases,
    creating a fresh database instance for each test to ensure isolation.
    All test classes should inherit from this to maintain consistency.
    
    Attributes:
        app: Flask application instance configured for testing
        client: Flask test client for making requests
        app_context: Application context used for database operations
    """
    def setUp(self):
        """
        Set up test environment before each test method runs.
        
        Creates a Flask application with testing configuration (using in-memory SQLite),
        initializes a test client, pushes an application context, and creates 
        all database tables.
        """
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """
        Clean up test environment after each test method completes.
        
        Removes the database session, drops all tables, disposes of the
        database engine connection pool, and pops the application context.
        This ensures a clean state for the next test.
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()    
        self.app_context.pop() 

    def force_login(self, user):
        """
        Manually set user session data to simulate a logged-in user.
        
        Args:
            user: User object to be used for session authentication
            
        Note:
            This bypasses the normal login flow to directly set session variables,
            useful for testing routes that require authentication.
        """
        with self.client.session_transaction() as sess:
            sess['name'] = user.name
            sess['_user_id'] = str(user.id)


# Example usage:
# from tests.base import FlaskTestBase
# class MyTest(FlaskTestBase):
#     def test_something(self):
#         ... 
