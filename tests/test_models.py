import unittest
from app.models import db, User, JobApplication
from tests.base import FlaskTestBase
from datetime import datetime, timezone

class TestModels(FlaskTestBase):
    """
    Tests for User and JobApplication models using a mock in-memory database.
    Inherits setup/teardown from FlaskTestBase for isolation.
    To add more tests, just add methods to this class.
    """
    def test_user_creation(self):
        user = User(name='modeluser', email='model@example.com', password='modelpass')
        db.session.add(user)
        db.session.commit()
        queried = User.query.filter_by(email='model@example.com').first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.name, 'modeluser')

    def test_job_application_creation(self):
        user = User(name='appuser', email='app@example.com', password='apppass')
        db.session.add(user)
        db.session.commit()
        app = JobApplication(
            title='Test Job',
            company='Test Co',
            location='Test City',
            job_type='Internship',
            closing_date=datetime.now(timezone.utc),
            status='Applied',
            user=user
        )
        db.session.add(app)
        db.session.commit()
        queried = JobApplication.query.filter_by(title='Test Job').first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.user_id, user.id)

    # Add more tests for relationships, updates, deletes, etc. as needed

if __name__ == '__main__':
    unittest.main() 