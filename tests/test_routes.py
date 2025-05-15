import unittest
from app.models import db, User
from tests.base import FlaskTestBase

class TestRoutes(FlaskTestBase):
    """
    Tests for major Flask routes using a mock in-memory database.
    Inherits setup/teardown from FlaskTestBase for isolation.
    To add more tests, just add methods to this class.
    """
    def setUp(self):
        super().setUp()
        # Create a test user
        user = User(name='testuser', email='test@example.com', password='testpass')
        db.session.add(user)
        db.session.commit()

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CareerLink', response.data)

    def test_signup_and_signin(self):
        # Signup
        response = self.client.post('/signup', data={
            'name': 'newuser', 'email': 'new@example.com', 'password': 'newpass'
        }, follow_redirects=True)
        self.assertIn(b'dashboard', response.data)
        # Signin
        response = self.client.post('/signin', data={
            'email': 'new@example.com', 'password': 'newpass'
        }, follow_redirects=True)
        self.assertIn(b'dashboard', response.data)

    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'CareerLink', response.data)

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess['name'] = 'testuser'
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'CareerLink', response.data)

    def test_job_search_requires_login(self):
        response = self.client.get('/job-search', follow_redirects=True)
        self.assertIn(b'CareerLink', response.data)

    def test_friend_requires_login(self):
        response = self.client.get('/comms', follow_redirects=True) # TODO: we need to change this url to friends
        self.assertIn(b'CareerLink', response.data)

    def login(self, email, password):
        response = self.client.post('/signin', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
        # Fail fast if login fails
        assert b'dashboard' in response.data or b'Dashboard' in response.data, 'Login failed!'
        return response

    def test_navigate_home(self):
        response = self.client.get('/')
        self.assertIn(b'CareerLink', response.data)

    def test_navigate_dashboard(self):
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/dashboard')
        self.assertIn(b'Dashboard', response.data)

    def test_navigate_job_search(self):
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/job-search')
        self.assertIn(b'Career Explorer', response.data)

    def test_navigate_analytics(self):
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/analytics')
        self.assertIn(b'Analytics', response.data)

    def test_navigate_job_tracker(self):
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/job-tracker')
        self.assertIn(b'Your Job Tracker', response.data)

    def test_navigate_comms(self):
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/comms')
        self.assertIn(b'Friends', response.data)

    # Add more tests for other routes and API endpoints as needed
    # For example, test /api/scraped-jobs, /add-application, etc.
    # To test authenticated endpoints, set session['name'] as above.

if __name__ == '__main__':
    unittest.main() 