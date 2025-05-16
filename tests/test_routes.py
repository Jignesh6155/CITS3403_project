"""
Route testing module for Flask application.

This module contains tests that verify the functionality of Flask routes,
including authentication flows, navigation, and access control. It simulates
HTTP requests and validates responses.
"""

import unittest
from app.models import db, User
from tests.base import FlaskTestBase

class TestRoutes(FlaskTestBase):
    """
    Tests for major Flask routes using a mock in-memory database.
    
    This test suite verifies that routes respond correctly to requests,
    including proper rendering, redirects, and access controls. It covers
    authentication flows, navigation, and authenticated route protection.
    """
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Calls the parent setUp method and creates a test user for route testing.
        """
        super().setUp()
        # Create a test user for authentication tests
        user = User(name='testuser', email='test@example.com', password='testpass')
        db.session.add(user)
        db.session.commit()

    def test_home(self):
        """
        Test the home route.
        
        Verifies that the home page loads correctly and contains
        expected content.
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)  # Check HTTP 200 OK status
        self.assertIn(b'CareerLink', response.data)  # Verify page contains site name

    def test_signup_and_signin(self):
        """
        Test the signup and signin routes.
        
        Verifies that users can register and subsequently sign in,
        and are redirected to the dashboard after authentication.
        """
        # Test signup process
        response = self.client.post('/signup', data={
            'name': 'newuser', 'email': 'new@example.com', 'password': 'newpass'
        }, follow_redirects=True)
        self.assertIn(b'dashboard', response.data)  # Should redirect to dashboard
        
        # Test signin process with newly created credentials
        response = self.client.post('/signin', data={
            'email': 'new@example.com', 'password': 'newpass'
        }, follow_redirects=True)
        self.assertIn(b'dashboard', response.data)  # Should redirect to dashboard

    def test_dashboard_requires_login(self):
        """
        Test that dashboard requires authentication.
        
        Verifies that unauthenticated users are redirected away from
        the dashboard to the login page.
        """
        response = self.client.get('/dashboard', follow_redirects=True)
        # Should redirect to login page (containing 'CareerLink' heading)
        self.assertIn(b'CareerLink', response.data)

    def test_logout(self):
        """
        Test the logout route.
        
        Verifies that logging out clears the session and redirects
        to the home page.
        """
        # Set up session first to simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['name'] = 'testuser'
            
        # Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'CareerLink', response.data)  # Should redirect to home

    def test_job_search_requires_login(self):
        """
        Test that job search requires authentication.
        
        Verifies that unauthenticated users are redirected away from
        the job search page to the login page.
        """
        response = self.client.get('/job-search', follow_redirects=True)
        # Should redirect to login page
        self.assertIn(b'CareerLink', response.data)

    def test_friend_requires_login(self):
        """
        Test that friends/comms page requires authentication.
        
        Verifies that unauthenticated users are redirected away from
        the communications page to the login page.
        
        Note:
            There appears to be a route naming inconsistency ('comms' vs 'friends')
            that should be addressed.
        """
        response = self.client.get('/comms', follow_redirects=True)  # TODO: we need to change this url to friends
        # Should redirect to login page
        self.assertIn(b'CareerLink', response.data)

    def login(self, email, password):
        """
        Helper method to log in a user for testing authenticated routes.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Flask response object from the login request
            
        Raises:
            AssertionError: If login fails
        """
        response = self.client.post('/signin', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
        # Fail fast if login fails to avoid misleading test failures
        assert b'dashboard' in response.data or b'Dashboard' in response.data, 'Login failed!'
        return response

    def test_navigate_home(self):
        """
        Test navigation to home page.
        
        Verifies that the home page loads correctly.
        """
        response = self.client.get('/')
        self.assertIn(b'CareerLink', response.data)

    def test_navigate_dashboard(self):
        """
        Test navigation to dashboard when authenticated.
        
        Verifies that an authenticated user can access the dashboard.
        """
        # Force login the test user
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        
        # Access dashboard
        response = self.client.get('/dashboard')
        self.assertIn(b'Dashboard', response.data)

    def test_navigate_job_search(self):
        """
        Test navigation to job search page when authenticated.
        
        Verifies that an authenticated user can access the job search page.
        """
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/job-search')
        self.assertIn(b'Career Explorer', response.data)

    def test_navigate_analytics(self):
        """
        Test navigation to analytics page when authenticated.
        
        Verifies that an authenticated user can access the analytics page.
        """
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/analytics')
        self.assertIn(b'Analytics', response.data)

    def test_navigate_job_tracker(self):
        """
        Test navigation to job tracker page when authenticated.
        
        Verifies that an authenticated user can access the job tracker page.
        """
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/job-tracker')
        self.assertIn(b'Your Job Tracker', response.data)

    def test_navigate_comms(self):
        """
        Test navigation to communications/friends page when authenticated.
        
        Verifies that an authenticated user can access the communications page.
        """
        user = User.query.filter_by(email='test@example.com').first()
        self.force_login(user)
        response = self.client.get('/comms')
        self.assertIn(b'Friends', response.data)

    # Add more tests for other routes and API endpoints as needed
    # For example, test /api/scraped-jobs, /add-application, etc.
    # To test authenticated endpoints, set session['name'] as above.

if __name__ == '__main__':
    unittest.main()
