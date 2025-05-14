import unittest
from app import create_app
from app.models import db, User
from app.config import TestingConfig

class TestRoutes(unittest.TestCase):
    def setUp(self):
        # Create app with testing config
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Create a test user
        user = User(name='testuser', email='test@example.com', password='testpass')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'index', response.data)

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
        self.assertIn(b'index', response.data)

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess['name'] = 'testuser'
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'index', response.data)

    def test_job_search_requires_login(self):
        response = self.client.get('/job-search', follow_redirects=True)
        self.assertIn(b'index', response.data)

    # Add more tests for other routes and API endpoints as needed
    # For example, test /api/scraped-jobs, /add-application, etc.
    # To test authenticated endpoints, set session['name'] as above.

if __name__ == '__main__':
    unittest.main() 