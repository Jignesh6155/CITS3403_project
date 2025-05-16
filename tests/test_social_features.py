"""
Social features test module for Flask application.

This module contains comprehensive tests for the social features of the application,
including friend requests, job application sharing, and account settings functionality.
It verifies the complete workflow of these features, including edge cases and error handling.
"""

from tests.base import FlaskTestBase
from app.models import db, User, JobApplication, FriendRequest, Notification
from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash

class TestSocialFeatures(FlaskTestBase):
    """
    Tests for social features including friend requests, application sharing,
    and account settings.
    
    This test suite covers the core social functionality of the application:
    1. Friend requests (sending, accepting, rejecting)
    2. Application sharing
    3. Saving shared applications
    4. Account settings (changing name and password)
    
    Each test validates both the HTTP responses and database state changes.
    """
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Creates two test users with hashed passwords and a job application
        that will be used for sharing tests.
        """
        super().setUp()
        
        # Create test users with properly hashed passwords for auth testing
        self.user1 = User(
            name='Alice', 
            email='alice@example.com', 
            password=generate_password_hash('alicepass')  # Secure password storage
        )
        self.user2 = User(
            name='Bob', 
            email='bob@example.com', 
            password=generate_password_hash('bobpass')
        )
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        
        # Create job application for user1 (will be used in sharing tests)
        self.job_app = JobApplication(
            title='Test Engineer',
            company='Test Co',
            location='Test City',
            job_type='Full-time',
            closing_date=datetime.now(timezone.utc),
            status='Applied',
            user_id=self.user1.id
        )
        db.session.add(self.job_app)
        db.session.commit()

    def test_send_friend_request(self):
        """
        Test sending a friend request.
        
        Verifies that:
        1. A user can send a friend request to another user
        2. A FriendRequest record is created with correct attributes
        3. A notification is created for the request recipient
        """
        # Log in as user1 (the sender)
        self.force_login(self.user1)
        
        # Send friend request from user1 to user2
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()  # Include CSRF protection
        }, follow_redirects=True)
        
        # Verify friend request was created in database
        friend_request = FriendRequest.query.filter_by(
            sender_id=self.user1.id,
            receiver_id=self.user2.id
        ).first()
        
        # Request should exist and have pending status
        self.assertIsNotNone(friend_request)
        self.assertEqual(friend_request.status, 'pending')
        
        # Verify notification was created for recipient
        notification = Notification.query.filter_by(
            user_id=self.user2.id,
            type='friend_request'
        ).first()
        
        # Notification should exist and mention sender's name
        self.assertIsNotNone(notification)
        self.assertIn(self.user1.name, notification.content)

    def test_accept_friend_request(self):
        """
        Test accepting a friend request.
        
        Verifies that:
        1. A recipient can accept a pending friend request
        2. The request status is updated to 'accepted'
        3. A bidirectional friendship is established in the database
        """
        # Create a pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user2 (receiver) to accept the request
        self.force_login(self.user2)
        
        # Accept the friend request
        response = self.client.post(f'/handle-friend-request/{friend_request.id}', data={
            'action': 'accept',
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify request was updated to accepted
        updated_request = db.session.get(FriendRequest, friend_request.id)
        self.assertEqual(updated_request.status, 'accepted')
        
        # Verify bidirectional friendship was established
        # Both users should appear in each other's friends list
        self.assertIn(self.user1, self.user2.friends.all())
        self.assertIn(self.user2, self.user1.friends.all())

    def test_reject_friend_request(self):
        """
        Test rejecting a friend request.
        
        Verifies that:
        1. A recipient can reject a pending friend request
        2. The request status is updated to 'rejected'
        3. No friendship is established between users
        """
        # Create a pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user2 (receiver) to reject the request
        self.force_login(self.user2)
        
        # Reject the friend request
        response = self.client.post(f'/handle-friend-request/{friend_request.id}', data={
            'action': 'reject',
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify request was updated to rejected
        updated_request = FriendRequest.query.filter_by(id=friend_request.id).first()
        self.assertEqual(updated_request.status, 'rejected')
        
        # Verify friendship was NOT established (negative test)
        self.assertNotIn(self.user1, self.user2.friends.all())
        self.assertNotIn(self.user2, self.user1.friends.all())

    def test_share_application(self):
        """
        Test sharing a job application with a friend.
        
        Verifies that:
        1. A user can share their job application with a friend
        2. An application_shares record is created
        3. A notification is created for the recipient
        """
        # First make the users friends (prerequisite for sharing)
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Log in as user1 (owner of the job application)
        self.force_login(self.user1)
        
        # Share the application with user2
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify application is shared in database
        # Check the application_shares table directly with SQL
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        # Share record should exist and be active
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'active')
        
        # Verify notification was created for recipient
        notification = Notification.query.filter_by(
            user_id=self.user2.id,
            type='application_shared'
        ).first()
        
        # Notification should exist and include relevant details
        self.assertIsNotNone(notification)
        self.assertIn(self.user1.name, notification.content)  # Sender name
        self.assertIn(self.job_app.company, notification.content)  # Job details

    def test_save_shared_application(self):
        """
        Test saving a shared application to user's own tracker.
        
        Verifies that:
        1. A user can save a shared application to their own tracker
        2. A new JobApplication record is created for the recipient
        3. The share status is updated to 'archived'
        """
        # First make the users friends (prerequisite)
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Create a sharing record directly (simulating a previous share)
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "active"}
        )
        db.session.commit()
        
        # Log in as user2 (recipient of the shared application)
        self.force_login(self.user2)
        
        # Save the shared application (simulating "Add to my tracker" action)
        response = self.client.post(f'/save-shared-application/{self.job_app.id}', 
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': self.get_csrf_token()  # CSRF token in header for AJAX
            },
            json={}  # Empty JSON body
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify a new application was created for user2
        new_app = JobApplication.query.filter_by(
            user_id=self.user2.id,
            title=self.job_app.title,
            company=self.job_app.company
        ).first()
        
        # New application should exist with correct status
        self.assertIsNotNone(new_app)
        self.assertEqual(new_app.status, 'Saved')  # Initial status for saved applications
        
        # Verify the share status is now 'archived' (to prevent duplicate saves)
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'archived')

    def test_update_name(self):
        """
        Test changing user's display name.
        
        Verifies that:
        1. A user can update their display name
        2. The name is updated in the database
        3. A notification is created confirming the change
        """
        # Log in as user1
        self.force_login(self.user1)
        
        # Submit name change request
        new_name = 'Alice Smith'
        response = self.client.post('/update-name', data={
            'new_name': new_name,
            'csrf_token': self.get_csrf_token()
        })
        
        # Verify API response is successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify name was updated in database
        updated_user = db.session.get(User, self.user1.id)
        self.assertEqual(updated_user.name, new_name)
        
        # Verify notification was created confirming the update
        notification = Notification.query.filter_by(
            user_id=self.user1.id,
            type='account_update'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(new_name, notification.content)  # Should mention new name

    def test_update_password(self):
        """
        Test changing user's password.
        
        Verifies that:
        1. A user can update their password with correct current password
        2. The password is updated in the database
        3. A notification is created confirming the change
        4. The user can log in with the new password
        """
        # Log in as user1
        self.force_login(self.user1)
        
        # Submit password change request
        current_password = 'alicepass'
        new_password = 'newpassword123'
        response = self.client.post('/update-password', data={
            'current_password': current_password,
            'new_password': new_password,
            'csrf_token': self.get_csrf_token()
        })
        
        # Verify API response is successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify notification was created confirming the update
        notification = Notification.query.filter_by(
            user_id=self.user1.id,
            type='account_update'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('password', notification.content.lower())  # Should mention password change
        
        # Verify can log in with new password (integration test)
        # First log out
        self.client.get('/logout')
        
        # Then try to log in with new password
        response = self.client.post('/signin', data={
            'email': self.user1.email,
            'password': new_password
        }, follow_redirects=True)
        
        # Should be redirected to dashboard on successful login
        self.assertIn(b'dashboard', response.data)

    def get_csrf_token(self):
        """
        Helper function to get CSRF token from page.
        
        Returns:
            str: CSRF token extracted from page HTML
            
        Note:
            This demonstrates how to extract security tokens from rendered HTML
            for testing protected forms/endpoints.
        """
        response = self.client.get('/')
        csrf_token = None
        # Parse response HTML to find CSRF token
        for line in response.data.decode().split('\n'):
            if 'csrf-token' in line:
                import re
                match = re.search('content="([^"]+)"', line)
                if match:
                    csrf_token = match.group(1)
                    break
        return csrf_token


class TestFriendRequestsEdgeCases(FlaskTestBase):
    """
    Test edge cases for friend requests feature.
    
    This test suite focuses on boundary conditions and error handling for
    the friend request system, ensuring the application handles invalid
    inputs and special cases correctly.
    """
    
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Creates three test users to test various friend request scenarios.
        """
        super().setUp()
        # Create test users
        self.user1 = User(name='Alice', email='alice@example.com', password='alicepass')
        self.user2 = User(name='Bob', email='bob@example.com', password='bobpass')
        self.user3 = User(name='Charlie', email='charlie@example.com', password='charliepass')
        db.session.add_all([self.user1, self.user2, self.user3])
        db.session.commit()

    def test_send_request_to_nonexistent_user(self):
        """
        Test sending a friend request to a non-existent user.
        
        Verifies that the application handles attempts to send friend requests
        to non-existent email addresses with appropriate error messages.
        """
        # Log in as user1
        self.force_login(self.user1)
        
        # Attempt to send request to non-existent email
        response = self.client.post('/send-friend-request', data={
            'email': 'nonexistent@example.com',  # Email not in database
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Should show error message about user not found
        self.assertIn(b'User not found', response.data)

    def test_send_request_to_self(self):
        """
        Test sending a friend request to oneself.
        
        Verifies that the application prevents users from sending
        friend requests to themselves.
        """
        # Log in as user1
        self.force_login(self.user1)
        
        # Attempt to send request to self (same email)
        response = self.client.post('/send-friend-request', data={
            'email': self.user1.email,  # Same as logged-in user
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Should show error about not being able to friend yourself
        self.assertIn(b'cannot send a friend request to yourself', response.data.lower())

    def test_send_duplicate_request(self):
        """
        Test sending a duplicate friend request.
        
        Verifies that the application prevents sending duplicate
        friend requests to the same user.
        """
        # Create an existing pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user1
        self.force_login(self.user1)
        
        # Attempt to send duplicate request
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Should show error about request already sent
        self.assertIn(b'Friend request already sent', response.data)

    def test_auto_accept_mutual_requests(self):
        """
        Test automatic acceptance of mutual friend requests.
        
        Verifies that when two users send requests to each other,
        the system automatically accepts both requests and establishes
        the friendship without requiring explicit acceptance.
        """
        # Create a pending friend request from user2 to user1
        friend_request = FriendRequest(
            sender_id=self.user2.id,
            receiver_id=self.user1.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user1
        self.force_login(self.user1)
        
        # Send request from user1 to user2 (creating mutual requests)
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify both users are now friends (bidirectional)
        self.assertIn(self.user2, self.user1.friends.all())
        self.assertIn(self.user1, self.user2.friends.all())
        
        # Verify the original request is now accepted
        updated_request = FriendRequest.query.filter_by(id=friend_request.id).first()
        self.assertEqual(updated_request.status, 'accepted')
        
        # Check for success message in response
        self.assertIn(f'You are now friends with {self.user2.name}'.encode(), response.data)

    def get_csrf_token(self):
        """
        Helper function to get CSRF token from page.
        
        Returns:
            str: CSRF token extracted from page HTML
        """
        response = self.client.get('/')
        csrf_token = None
        for line in response.data.decode().split('\n'):
            if 'csrf-token' in line:
                import re
                match = re.search('content="([^"]+)"', line)
                if match:
                    csrf_token = match.group(1)
                    break
        return csrf_token


class TestSharingEdgeCases(FlaskTestBase):
    """
    Test edge cases for application sharing feature.
    
    This test suite focuses on boundary conditions and error handling
    for the job application sharing system, ensuring the application
    handles special cases correctly.
    """
    
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Creates two test users and a job application for sharing tests.
        """
        super().setUp()
        # Create test users
        self.user1 = User(name='Alice', email='alice@example.com', password='alicepass')
        self.user2 = User(name='Bob', email='bob@example.com', password='bobpass')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        
        # Create job application for user1
        self.job_app = JobApplication(
            title='Test Engineer',
            company='Test Co',
            location='Test City',
            job_type='Full-time',
            closing_date=datetime.now(timezone.utc),
            status='Applied',
            user_id=self.user1.id
        )
        db.session.add(self.job_app)
        db.session.commit()

    def test_reshare_already_shared_application(self):
        """
        Test resharing an already shared application.
        
        Verifies that the application prevents sharing the same
        application to the same friend multiple times.
        """
        # Make users friends (prerequisite)
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Create existing active share record
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "active"}
        )
        db.session.commit()
        
        # Log in as user1 (owner)
        self.force_login(self.user1)
        
        # Try to share again
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Should show error about already shared
        self.assertIn(b'Application already shared with this friend', response.data)

    def test_reactivate_archived_share(self):
        """
        Test resharing an archived shared application.
        
        Verifies that if a previously shared application was archived
        (e.g., after saving), it can be re-shared and reactivated.
        """
        # Make users friends (prerequisite)
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Create existing archived share record
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "archived"}
        )
        db.session.commit()
        
        # Log in as user1 (owner)
        self.force_login(self.user1)
        
        # Try to share again (should reactivate)
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Should show success message about re-sharing
        self.assertIn(b're-shared', response.data)
        
        # Verify share is now active
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'active')  # Status should be changed back to active

    def get_csrf_token(self):
        """
        Helper function to get CSRF token from page.
        
        Returns:
            str: CSRF token extracted from page HTML
        """
        response = self.client.get('/')
        csrf_token = None
        for line in response.data.decode().split('\n'):
            if 'csrf-token' in line:
                import re
                match = re.search('content="([^"]+)"', line)
                if match:
                    csrf_token = match.group(1)
                    break
        return csrf_token


class TestAccountSettingsEdgeCases(FlaskTestBase):
    """
    Test edge cases for account settings feature.
    
    This test suite focuses on boundary conditions and error handling
    for the account settings system, ensuring the application validates
    inputs and handles errors appropriately.
    """
    
    def setUp(self):
        """
        Set up test data before each test method runs.
        
        Creates a test user for account settings tests.
        """
        super().setUp()
        # Create test user
        self.user = User(name='Alice', email='alice@example.com', password='alicepass')
        db.session.add(self.user)
        db.session.commit()

    def test_update_name_blank(self):
        """
        Test updating to a blank name.
        
        Verifies that the application prevents users from setting
        an empty name and provides appropriate error feedback.
        """
        # Log in as the test user
        self.force_login(self.user)
        
        # Attempt to update name to empty string
        response = self.client.post('/update-name', data={
            'new_name': '',  # Empty name
            'csrf_token': self.get_csrf_token()
        })
        
        # Parse JSON response
        data = json.loads(response.data)
        self.assertFalse(data['success'])  # Should fail
        self.assertIn('required', data['message'].lower())  # Error about required field
        
        # Verify name didn't change in database
        updated_user = db.session.get(User, self.user.id)
        self.assertEqual(updated_user.name, 'Alice')  # Original name should be preserved

    def test_update_password_wrong_current(self):
        """
        Test updating password with wrong current password.
        
        Verifies that the application requires correct current password
        verification before allowing password changes.
        """
        # Log in as the test user
        self.force_login(self.user)
        
        # Attempt password change with incorrect current password
        response = self.client.post('/update-password', data={
            'current_password': 'wrongpassword',  # Incorrect password
            'new_password': 'newpassword123',
            'csrf_token': self.get_csrf_token()
        })
        
        # Parse JSON response
        data = json.loads(response.data)
        self.assertFalse(data['success'])  # Should fail
        self.assertIn('incorrect', data['message'].lower())  # Error about incorrect password

    def test_update_password_missing_fields(self):
        """
        Test updating password with missing fields.
        
        Verifies that the application validates required fields
        for password changes.
        """
        # Log in as the test user
        self.force_login(self.user)
        
        # Attempt password change with missing new password
        response = self.client.post('/update-password', data={
            'current_password': 'alicepass',  # Correct current password
            # Missing new_password field
            'csrf_token': self.get_csrf_token()
        })
        
        # Parse JSON response
        data = json.loads(response.data)
        self.assertFalse(data['success'])  # Should fail
        self.assertIn('required', data['message'].lower())  # Error about required field

    def get_csrf_token(self):
        """
        Helper function to get CSRF token from page.
        
        Returns:
            str: CSRF token extracted from page HTML
        """
        response = self.client.get('/')
        csrf_token = None
        for line in response.data.decode().split('\n'):
            if 'csrf-token' in line:
                import re
                match = re.search('content="([^"]+)"', line)
                if match:
                    csrf_token = match.group(1)
                    break
        return csrf_token


if __name__ == '__main__':
    import unittest
    unittest.main()
