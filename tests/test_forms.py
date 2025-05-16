"""
Form validation tests for Flask application routes.

This module contains tests for validating form submissions and verifying 
appropriate server responses. It covers signup, signin, and application 
form validation including error messages for invalid inputs.
"""

from tests.base import FlaskTestBase
from app.models import db, User, JobApplication
from datetime import datetime

class TestFormValidation(FlaskTestBase):
    """
    Tests for form validation logic in Flask routes (signup, signin, add-application, etc.).
    
    This test suite verifies that form validation works correctly for all major
    application forms, including required field validation, duplicate checks,
    and other validation rules. It simulates form submissions and checks the
    expected feedback messages.
    """
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Calls the parent setUp method and creates a test user for form validation tests.
        """
        super().setUp()
        user = User(name='formuser', email='form@example.com', password='formpass')
        db.session.add(user)
        db.session.commit()

    def test_signup_missing_fields(self):
        """
        Test signup form validation for missing required fields.
        
        Verifies that the application properly validates and rejects form submissions
        when required fields (name, email, password) are missing.
        """
        # Missing name
        resp = self.client.post('/signup', data={'email': 'a@b.com', 'password': 'x'}, follow_redirects=True)
        self.assertIn(b'All fields are required', resp.data)
        # Missing email
        resp = self.client.post('/signup', data={'name': 'A', 'password': 'x'}, follow_redirects=True)
        self.assertIn(b'All fields are required', resp.data)
        # Missing password
        resp = self.client.post('/signup', data={'name': 'A', 'email': 'a@b.com'}, follow_redirects=True)
        self.assertIn(b'All fields are required', resp.data)

    def test_signup_duplicate_email(self):
        """
        Test signup form validation for duplicate email addresses.
        
        Verifies that the application correctly detects and rejects
        signup attempts with already registered email addresses.
        """
        resp = self.client.post('/signup', data={'name': 'A', 'email': 'form@example.com', 'password': 'x'}, follow_redirects=True)
        self.assertIn(b'Email already registered', resp.data)

    def test_signin_missing_fields(self):
        """
        Test signin form validation for missing required fields.
        
        Verifies that the application properly validates and rejects signin
        attempts when required fields are missing.
        """
        resp = self.client.post('/signin', data={'email': '', 'password': ''}, follow_redirects=True)
        self.assertIn(b'All fields are required', resp.data)

    def test_signin_invalid(self):
        """
        Test signin form validation for invalid credentials.
        
        Verifies that the application correctly rejects signin attempts
        with nonexistent email or wrong password combinations.
        """
        resp = self.client.post('/signin', data={'email': 'no@no.com', 'password': 'bad'}, follow_redirects=True)
        self.assertIn(b'Invalid Email or Password', resp.data)

    def test_add_application_missing_fields(self):
        """
        Test add-application form validation for missing required fields.
        
        Simulates a logged-in user and verifies that the application form
        correctly validates required fields.
        
        Note: 
            Current implementation only tests session authentication without
            testing field validation (commented code).
        """
        with self.client.session_transaction() as sess:
            sess['name'] = 'formuser'
        # # Missing title
        # resp = self.client.post('/add-application', data={'company': 'C'}, follow_redirects=True)
        # self.assertIn(b'Please fill in', resp.data)
        # # Missing company
        # resp = self.client.post('/add-application', data={'title': 'T'}, follow_redirects=True)
        # self.assertIn(b'Please fill in', resp.data)

    # Add more tests for other forms and validation logic as needed

if __name__ == '__main__':
    import unittest
    unittest.main() 
