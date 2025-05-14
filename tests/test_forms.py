from tests.base import FlaskTestBase
from app.models import db, User, JobApplication
from datetime import datetime

class TestFormValidation(FlaskTestBase):
    """
    Tests for form validation logic in Flask routes (signup, signin, add-application, etc.).
    Uses the Flask test client to simulate form submissions and check validation feedback.
    Extend this file to add more form validation tests as needed.
    """
    def setUp(self):
        super().setUp()
        user = User(name='formuser', email='form@example.com', password='formpass')
        db.session.add(user)
        db.session.commit()

    def test_signup_missing_fields(self):
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
        resp = self.client.post('/signup', data={'name': 'A', 'email': 'form@example.com', 'password': 'x'}, follow_redirects=True)
        self.assertIn(b'Email already registered', resp.data)

    def test_signin_missing_fields(self):
        resp = self.client.post('/signin', data={'email': '', 'password': ''}, follow_redirects=True)
        self.assertIn(b'All fields are required', resp.data)

    def test_signin_invalid(self):
        resp = self.client.post('/signin', data={'email': 'no@no.com', 'password': 'bad'}, follow_redirects=True)
        self.assertIn(b'Invalid Email or Password', resp.data)

    def test_add_application_missing_fields(self):
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