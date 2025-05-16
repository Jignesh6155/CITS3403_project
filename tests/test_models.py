"""
Database model tests for Flask application.

This module tests the database models (User and JobApplication) using a mock in-memory
SQLite database. It verifies that models can be properly created, saved, and retrieved
with correct relationships maintained.
"""

import unittest
from app.models import db, User, JobApplication
from tests.base import FlaskTestBase
from datetime import datetime, timezone

class TestModels(FlaskTestBase):
    """
    Tests for User and JobApplication models using a mock in-memory database.
    
    This test suite verifies that the database models function correctly,
    including object creation, database operations, and relationship handling.
    Each test runs in isolation using the in-memory database setup from FlaskTestBase.
    """
    def test_user_creation(self):
        """
        Test User model creation and database persistence.
        
        Verifies that a User object can be created, saved to the database,
        and retrieved with all attributes intact.
        """
        # Create and save a new user
        user = User(name='modeluser', email='model@example.com', password='modelpass')
        db.session.add(user)
        db.session.commit()
        
        # Query the user and verify persistence
        queried = User.query.filter_by(email='model@example.com').first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.name, 'modeluser')

    def test_job_application_creation(self):
        """
        Test JobApplication model creation and relationship with User.
        
        Verifies that a JobApplication object can be created with a relationship
        to a User, saved to the database, and retrieved with the relationship intact.
        """
        # Create a user for the relationship
        user = User(name='appuser', email='app@example.com', password='apppass')
        db.session.add(user)
        db.session.commit()
        
        # Create a job application linked to the user
        app = JobApplication(
            title='Test Job',
            company='Test Co',
            location='Test City',
            job_type='Internship',
            closing_date=datetime.now(timezone.utc),
            status='Applied',
            user=user  # Set relationship through ORM
        )
        db.session.add(app)
        db.session.commit()
        
        # Query and verify the application and its relationship
        queried = JobApplication.query.filter_by(title='Test Job').first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.user_id, user.id)  # Verify foreign key is set correctly

    # Add more tests for relationships, updates, deletes, etc. as needed

if __name__ == '__main__':
    unittest.main()
