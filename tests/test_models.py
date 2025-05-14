import unittest
from app import create_app
from app.models import db, User, JobApplication
from app.config import TestingConfig
from datetime import datetime

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

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
            closing_date=datetime.utcnow(),
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