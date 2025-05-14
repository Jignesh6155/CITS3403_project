from tests.base import FlaskTestBase
from app.models import db, User, JobApplication, JobSearch, ScrapedJob, ResumeAnalysis, FriendRequest, Notification
from datetime import datetime

class TestSampleData(FlaskTestBase):
    """
    Tests that insert and verify realistic sample data for all major models.
    Use this as a template for adding more comprehensive integration or data tests.
    """
    def setUp(self):
        super().setUp()
        # Create users
        self.user1 = User(name='Alice', email='alice@example.com', password='alicepass')
        self.user2 = User(name='Bob', email='bob@example.com', password='bobpass')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        # Create a job search
        self.job_search = JobSearch(search_query='engineer', results='[]', user_id=self.user1.id)
        db.session.add(self.job_search)
        db.session.commit()
        # Create a scraped job
        self.scraped_job = ScrapedJob(
            user_id=self.user1.id,
            title='Graduate Software Engineer',
            posted_date='2024-06-01',
            closing_in='10 days',
            closing_date=datetime.utcnow(),
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
        # Create a job application
        self.job_app = JobApplication(
            title='Graduate Software Engineer',
            company='Tech Corp',
            location='Perth',
            job_type='Graduate',
            closing_date=datetime.utcnow(),
            status='Applied',
            user_id=self.user1.id,
            scraped_job_id=self.scraped_job.id
        )
        db.session.add(self.job_app)
        db.session.commit()
        # Create a resume analysis
        self.resume = ResumeAnalysis(
            user_id=self.user1.id,
            filename='resume.pdf',
            content_type='application/pdf',
            raw_text='Alice resume text',
            keywords='["Python", "Software"]',
            suggested_jobs='[1]'
        )
        db.session.add(self.resume)
        db.session.commit()
        # Create a friend request
        self.friend_request = FriendRequest(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            status='pending'
        )
        db.session.add(self.friend_request)
        db.session.commit()
        # Create a notification
        self.notification = Notification(
            user_id=self.user1.id,
            content='Welcome to the platform!',
            type='general',
            is_read=False
        )
        db.session.add(self.notification)
        db.session.commit()

    def test_users_exist(self):
        self.assertEqual(User.query.count(), 2)
        self.assertEqual(User.query.filter_by(name='Alice').first().email, 'alice@example.com')

    def test_job_search(self):
        js = JobSearch.query.first()
        self.assertEqual(js.search_query, 'engineer')
        self.assertEqual(js.user_id, self.user1.id)

    def test_scraped_job(self):
        sj = ScrapedJob.query.first()
        self.assertEqual(sj.title, 'Graduate Software Engineer')
        self.assertEqual(sj.user_id, self.user1.id)

    def test_job_application(self):
        app = JobApplication.query.first()
        self.assertEqual(app.company, 'Tech Corp')
        self.assertEqual(app.user_id, self.user1.id)
        self.assertEqual(app.scraped_job_id, self.scraped_job.id)

    def test_resume_analysis(self):
        ra = ResumeAnalysis.query.first()
        self.assertEqual(ra.filename, 'resume.pdf')
        self.assertIn('Python', ra.keywords)

    def test_friend_request(self):
        fr = FriendRequest.query.first()
        self.assertEqual(fr.sender_id, self.user1.id)
        self.assertEqual(fr.receiver_id, self.user2.id)
        self.assertEqual(fr.status, 'pending')

    def test_notification(self):
        n = Notification.query.first()
        self.assertEqual(n.user_id, self.user1.id)
        self.assertIn('Welcome', n.content)

    # To add more sample data or tests, extend setUp or add new test methods.

if __name__ == '__main__':
    import unittest
    unittest.main() 