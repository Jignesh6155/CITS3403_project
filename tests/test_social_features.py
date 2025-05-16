from tests.base import FlaskTestBase
from app.models import db, User, JobApplication, FriendRequest, Notification
from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash

class TestSocialFeatures(FlaskTestBase):
    """
    Tests for social features including friend requests, application sharing,
    and account settings.
    
    Covers:
    1. Friend requests (sending, accepting, rejecting)
    2. Application sharing
    3. Saving shared applications
    4. Account settings (changing name and password)
    """
    def setUp(self):
        super().setUp()
        # Create test users with hashed passwords
        self.user1 = User(
            name='Alice', 
            email='alice@example.com', 
            password=generate_password_hash('alicepass')
        )
        self.user2 = User(
            name='Bob', 
            email='bob@example.com', 
            password=generate_password_hash('bobpass')
        )
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

    def test_send_friend_request(self):
        """Test sending a friend request."""
        # Log in as user1
        self.force_login(self.user1)
        
        # Send friend request from user1 to user2
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify friend request was created
        friend_request = FriendRequest.query.filter_by(
            sender_id=self.user1.id,
            receiver_id=self.user2.id
        ).first()
        
        self.assertIsNotNone(friend_request)
        self.assertEqual(friend_request.status, 'pending')
        
        # Verify notification was created
        notification = Notification.query.filter_by(
            user_id=self.user2.id,
            type='friend_request'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.user1.name, notification.content)

    def test_accept_friend_request(self):
        """Test accepting a friend request."""
        # Create a pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user2 (receiver)
        self.force_login(self.user2)
        
        # Accept the friend request
        response = self.client.post(f'/handle-friend-request/{friend_request.id}', data={
            'action': 'accept',
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify request was accepted
        updated_request = FriendRequest.query.get(friend_request.id)
        self.assertEqual(updated_request.status, 'accepted')
        
        # Verify friendship was established (both ways)
        self.assertIn(self.user1, self.user2.friends.all())
        self.assertIn(self.user2, self.user1.friends.all())

    def test_reject_friend_request(self):
        """Test rejecting a friend request."""
        # Create a pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user2 (receiver)
        self.force_login(self.user2)
        
        # Reject the friend request
        response = self.client.post(f'/handle-friend-request/{friend_request.id}', data={
            'action': 'reject',
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify request was rejected
        updated_request = FriendRequest.query.get(friend_request.id)
        self.assertEqual(updated_request.status, 'rejected')
        
        # Verify friendship was NOT established
        self.assertNotIn(self.user1, self.user2.friends.all())
        self.assertNotIn(self.user2, self.user1.friends.all())

    def test_share_application(self):
        """Test sharing a job application with a friend."""
        # First make the users friends
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
        
        # Verify application is shared
        # Check the application_shares table
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'active')
        
        # Verify notification was created
        notification = Notification.query.filter_by(
            user_id=self.user2.id,
            type='application_shared'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.user1.name, notification.content)
        self.assertIn(self.job_app.company, notification.content)

    def test_save_shared_application(self):
        """Test saving a shared application to your own tracker."""
        # First make the users friends
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Share application with user2
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "active"}
        )
        db.session.commit()
        
        # Log in as user2
        self.force_login(self.user2)
        
        # Save the shared application
        response = self.client.post(f'/save-shared-application/{self.job_app.id}', 
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': self.get_csrf_token()
            },
            json={}
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
        
        self.assertIsNotNone(new_app)
        self.assertEqual(new_app.status, 'Saved')
        
        # Verify the share status is now 'archived'
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'archived')

    def test_update_name(self):
        """Test changing user's name."""
        # Log in as user1
        self.force_login(self.user1)
        
        # Change name
        new_name = 'Alice Smith'
        response = self.client.post('/update-name', data={
            'new_name': new_name,
            'csrf_token': self.get_csrf_token()
        })
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify name was updated in database
        updated_user = User.query.get(self.user1.id)
        self.assertEqual(updated_user.name, new_name)
        
        # Verify notification was created
        notification = Notification.query.filter_by(
            user_id=self.user1.id,
            type='account_update'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(new_name, notification.content)

    def test_update_password(self):
        """Test changing user's password."""
        # Log in as user1
        self.force_login(self.user1)
        
        # Change password
        current_password = 'alicepass'
        new_password = 'newpassword123'
        response = self.client.post('/update-password', data={
            'current_password': current_password,
            'new_password': new_password,
            'csrf_token': self.get_csrf_token()
        })
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify notification was created
        notification = Notification.query.filter_by(
            user_id=self.user1.id,
            type='account_update'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('password', notification.content.lower())
        
        # Verify can log in with new password (test sign out and sign in again)
        self.client.get('/logout')
        
        response = self.client.post('/signin', data={
            'email': self.user1.email,
            'password': new_password
        }, follow_redirects=True)
        
        self.assertIn(b'dashboard', response.data)

    def get_csrf_token(self):
        """Helper function to get CSRF token."""
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


class TestFriendRequestsEdgeCases(FlaskTestBase):
    """Test edge cases for friend requests feature."""
    
    def setUp(self):
        super().setUp()
        # Create test users
        self.user1 = User(name='Alice', email='alice@example.com', password='alicepass')
        self.user2 = User(name='Bob', email='bob@example.com', password='bobpass')
        self.user3 = User(name='Charlie', email='charlie@example.com', password='charliepass')
        db.session.add_all([self.user1, self.user2, self.user3])
        db.session.commit()

    def test_send_request_to_nonexistent_user(self):
        """Test sending a friend request to a non-existent user."""
        self.force_login(self.user1)
        
        response = self.client.post('/send-friend-request', data={
            'email': 'nonexistent@example.com',
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        self.assertIn(b'User not found', response.data)

    def test_send_request_to_self(self):
        """Test sending a friend request to oneself."""
        self.force_login(self.user1)
        
        response = self.client.post('/send-friend-request', data={
            'email': self.user1.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        self.assertIn(b'cannot send a friend request to yourself', response.data.lower())

    def test_send_duplicate_request(self):
        """Test sending a duplicate friend request."""
        # Create a pending friend request
        friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(friend_request)
        db.session.commit()
        
        # Log in as user1
        self.force_login(self.user1)
        
        # Send duplicate request
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        self.assertIn(b'Friend request already sent', response.data)

    def test_auto_accept_mutual_requests(self):
        """Test that mutual friend requests auto-accept."""
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
        
        # Send request from user1 to user2
        response = self.client.post('/send-friend-request', data={
            'email': self.user2.email,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Verify both users are now friends
        self.assertIn(self.user2, self.user1.friends.all())
        self.assertIn(self.user1, self.user2.friends.all())
        
        # Verify the original request is now accepted
        updated_request = FriendRequest.query.get(friend_request.id)
        self.assertEqual(updated_request.status, 'accepted')
        
        # Check for success message
        self.assertIn(f'You are now friends with {self.user2.name}'.encode(), response.data)

    def get_csrf_token(self):
        """Helper function to get CSRF token."""
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
    """Test edge cases for application sharing feature."""
    
    def setUp(self):
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

    def test_share_application_with_non_friend(self):
        """Test sharing an application with a non-friend."""
        # Log in as user1
        self.force_login(self.user1)
        
        # Share application with user2 (who is not a friend)
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        })
        
        # Check error message in JSON response
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Friend not found')
        
        # Verify no sharing relationship was created
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNone(result)

    def test_reshare_already_shared_application(self):
        """Test resharing an already shared application."""
        # Make users friends
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Share application once
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "active"}
        )
        db.session.commit()
        
        # Log in as user1
        self.force_login(self.user1)
        
        # Try to share again
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Check error message
        self.assertIn(b'Application already shared with this friend', response.data)

    def test_reactivate_archived_share(self):
        """Test resharing an archived shared application."""
        # Make users friends
        self.user1.friends.append(self.user2)
        self.user2.friends.append(self.user1)
        db.session.commit()
        
        # Share application once with archived status
        from sqlalchemy import text
        db.session.execute(
            text("INSERT INTO application_shares (user_id, job_application_id, status) VALUES (:user_id, :app_id, :status)"),
            {"user_id": self.user2.id, "app_id": self.job_app.id, "status": "archived"}
        )
        db.session.commit()
        
        # Log in as user1
        self.force_login(self.user1)
        
        # Share again (should reactivate)
        response = self.client.post(f'/share-application/{self.job_app.id}', data={
            'friend_id': self.user2.id,
            'csrf_token': self.get_csrf_token()
        }, follow_redirects=True)
        
        # Check success message
        self.assertIn(b're-shared', response.data)
        
        # Verify share is now active
        result = db.session.execute(
            text("SELECT * FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": self.user2.id, "app_id": self.job_app.id}
        ).fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'active')

    def get_csrf_token(self):
        """Helper function to get CSRF token."""
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
    """Test edge cases for account settings feature."""
    
    def setUp(self):
        super().setUp()
        # Create test user
        self.user = User(name='Alice', email='alice@example.com', password='alicepass')
        db.session.add(self.user)
        db.session.commit()

    def test_update_name_blank(self):
        """Test updating to a blank name."""
        self.force_login(self.user)
        
        response = self.client.post('/update-name', data={
            'new_name': '',
            'csrf_token': self.get_csrf_token()
        })
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('required', data['message'].lower())
        
        # Verify name didn't change
        updated_user = User.query.get(self.user.id)
        self.assertEqual(updated_user.name, 'Alice')

    def test_update_password_wrong_current(self):
        """Test updating password with wrong current password."""
        self.force_login(self.user)
        
        response = self.client.post('/update-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'csrf_token': self.get_csrf_token()
        })
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('incorrect', data['message'].lower())

    def test_update_password_missing_fields(self):
        """Test updating password with missing fields."""
        self.force_login(self.user)
        
        response = self.client.post('/update-password', data={
            'current_password': 'alicepass',
            'csrf_token': self.get_csrf_token()
        })
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('required', data['message'].lower())

    def get_csrf_token(self):
        """Helper function to get CSRF token."""
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