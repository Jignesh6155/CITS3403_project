"""
Sample data test module for Flask application.

This module tests the integration between all major models by creating
and verifying realistic sample data. It ensures that all models work together
correctly and verifies database relationships across the system.
"""

from tests.base import FlaskTestBase
from app.models import db, User, JobApplication, JobSearch, ScrapedJob, ResumeAnalysis, FriendRequest, Notification
from datetime import datetime, timezone
import warnings

# Suppress resource and deprecation warnings to keep test output clean
warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", DeprecationWarning)

class TestSampleData(FlaskTestBase):
    """
    Tests that insert and verify realistic sample data for all major models.
    
    This test suite creates a comprehensive set of interconnected model instances
    to verify that all models and their relationships function correctly together.
    It provides a template for creating more comprehensive integration tests.
    """
    def setUp(self):
        """
        Set up complex test data for all models before each test method runs.
        
        Creates a network of related model instances including:
        - Users 
        - Job search
        - Scraped job posting
        - Job application (linked to user and scraped job)
        - Resume analysis
        - Friend request between users
        - Notification
        """
        super().setUp()
        
        # Create test users
        self.user1 = User(name='Alice', email='alice@example.com', password='alicepass')
        self.user2 = User(name='Bob', email='bob@example.com', password='bobpass')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        
        # Create a job search record linked to user1
        self.job_search = JobSearch(search_query='engineer', results='[]', user_id=self.user1.id)
        db.session.add(self.job_search)
        db.session.commit()
        
        # Create a scraped job record linked to user1
        self.scraped_job = ScrapedJob(
            user_id=self.user1.id,
            title='Graduate Software Engineer',
            posted_date='2024-06-01',
            closing_in='10 days',
            closing_date=datetime.now(timezone.utc),
            ai_summary='Great job for new grads.',
            overview='["Develop software"]',
            responsibilities='["Write code"]',
            requirements='["Python"]',
            skills_and_qualities='["Teamwork"]',
            salary_info='["$70k"]',
            about_company='["Tech Corp"]',
            full_text='Full job description here.',
            link='http://example.com/job',
            source='GradConnection',
            tag_location='Perth',
            tag_jobtype='Graduate',
            tag_category='Engineering'
        )
        db.session.add(self.scraped_job)
        db.session.commit()
        
        # Create a job application linked to both user1 and the scraped job
        self.job_app = JobApplication(
            title='Graduate Software Engineer',
            company='Tech Corp',
            location='Perth',
            job_type='Graduate',
            closing_date=datetime.now(timezone.utc),
            status='Applied',
            user_id=self.user1.id,
            scraped_job_id=self.scraped_job.id
        )
        db.session.add(self.job_app)
        db.session.commit()
        
        # Create a resume analysis record for user1
        self.resume = ResumeAnalysis(
            user_id=self.user1.id,
            filename='resume.pdf',
            content_type='application/pdf',
            raw_text='Alice resume text',
            keywords='["Python", "Software"]',
            suggested_jobs='[1]'  # References job_id 1
        )
        db.session.add(self.resume)
        db.session.commit()
        
        # Create a friend request from user1 to user2
        self.friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(self.friend_request)
        db.session.commit()
        
        # Create a notification for user1
        self.notification = Notification(
            user_id=self.user1.id,
            content='Welcome to the platform!',
            type='general',
            is_read=False
        )
        db.session.add(self.notification)
        db.session.commit()

    def test_users_exist(self):
        """
        Test that users were correctly created and can be queried.
        
        Verifies that the expected number of users exists and the attributes
        are correctly persisted.
        """
        self.assertEqual(User.query.count(), 2)  # Should have exactly 2 users
        self.assertEqual(User.query.filter_by(name='Alice').first().email, 'alice@example.com')

    def test_job_search(self):
        """
        Test that job search record was correctly created.
        
        Verifies that the job search record has expected attributes and
        is correctly associated with a user.
        """
        js = JobSearch.query.first()
        self.assertEqual(js.search_query, 'engineer')
        self.assertEqual(js.user_id, self.user1.id)  # Verify user association

    def test_scraped_job(self):
        """
        Test that scraped job record was correctly created.
        
        Verifies that the scraped job record has expected attributes
        and is correctly associated with a user.
        """
        sj = ScrapedJob.query.first()
        self.assertEqual(sj.title, 'Graduate Software Engineer')
        self.assertEqual(sj.user_id, self.user1.id)  # Verify user association

    def test_job_application(self):
        """
        Test that job application was correctly created with relationships.
        
        Verifies that the job application has expected attributes and is
        correctly associated with both a user and a scraped job.
        """
        app = JobApplication.query.first()
        self.assertEqual(app.company, 'Tech Corp')
        self.assertEqual(app.user_id, self.user1.id)  # Verify user association
        self.assertEqual(app.scraped_job_id, self.scraped_job.id)  # Verify scraped job association

    def test_resume_analysis(self):
        """
        Test that resume analysis was correctly created.
        
        Verifies that the resume analysis record has expected attributes,
        including proper JSON field handling for keywords.
        """
        ra = ResumeAnalysis.query.first()
        self.assertEqual(ra.filename, 'resume.pdf')
        self.assertIn('Python', ra.keywords)  # Verify JSON string parsing

    def test_friend_request(self):
        """
        Test that friend request was correctly created.
        
        Verifies that the friend request has expected attributes and
        relationships to sender and receiver users.
        """
        fr = FriendRequest.query.first()
        self.assertEqual(fr.sender_id, self.user1.id)  # Verify sender association
        self.assertEqual(fr.receiver_id, self.user2.id)  # Verify receiver association
        self.assertEqual(fr.status, 'pending')  # Verify initial status

    def test_notification(self):
        """
        Test that notification was correctly created.
        
        Verifies that the notification has expected attributes and
        is correctly associated with a user.
        """
        n = Notification.query.first()
        self.assertEqual(n.user_id, self.user1.id)  # Verify user association
        self.assertIn('Welcome', n.content)  # Verify content

    # To add more sample data or tests, extend setUp or add new test methods.

if __name__ == '__main__':
    import unittest
    unittest.main()
