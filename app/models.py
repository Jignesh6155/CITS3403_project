from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import pytz

db = SQLAlchemy()

# Association table for sharing job applications between users
application_shares = db.Table('application_shares',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('job_application_id', db.Integer, db.ForeignKey('job_application.id'), primary_key=True),
    db.Column('status', db.String(20), default='active')  # Add this line
)

# Association table for user friendships
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Relationships
    job_applications = db.relationship('JobApplication', backref='user', lazy=True)
    job_searches = db.relationship('JobSearch', backref='user', lazy=True)
    scraped_jobs = db.relationship('ScrapedJob', backref='user', lazy=True)
    shared_applications = db.relationship(
        'JobApplication',
        secondary=application_shares,
        backref=db.backref('shared_with', lazy='dynamic')
    )
    # Friends relationship (self-referential many-to-many)
    friends = db.relationship(
        'User',
        secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref=db.backref('friend_of', lazy='dynamic'),
        lazy='dynamic'
    )

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(100))
    closing_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='Applied')
    date_applied = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scraped_job_id = db.Column(db.Integer, db.ForeignKey('scraped_job.id'))
    
    # Define the relationship to ScrapedJob only
    scraped_job = db.relationship('ScrapedJob', backref=db.backref('applications', lazy=True))

    def __repr__(self):
        return f'<JobApplication {self.title} at {self.company}>'

class JobSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255))
    results = db.Column(db.Text)  # JSON or text
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ScrapedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255))
    posted_date = db.Column(db.String(64))
    closing_in = db.Column(db.String(64))
    closing_date = db.Column(db.DateTime, nullable=True)  # New field for actual closing date
    ai_summary = db.Column(db.Text)
    overview = db.Column(db.Text)  # JSON stringified list
    responsibilities = db.Column(db.Text)  # JSON stringified list
    requirements = db.Column(db.Text)  # JSON stringified list
    skills_and_qualities = db.Column(db.Text)  # JSON stringified list
    salary_info = db.Column(db.Text)  # JSON stringified list
    about_company = db.Column(db.Text)  # JSON stringified list
    full_text = db.Column(db.Text)
    link = db.Column(db.String(512))
    source = db.Column(db.String(120))
    tag_location = db.Column(db.String(120))
    tag_jobtype = db.Column(db.String(120))
    tag_category = db.Column(db.String(120))

class ResumeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255))
    content_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    raw_text = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON stringified list of extracted keywords
    suggested_jobs = db.Column(db.Text)  # JSON stringified list of job IDs

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_requests', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_requests', lazy='dynamic'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)  
    type = db.Column(db.String(50), nullable=False)  # e.g., 'friend_request', 'job_application_update', etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to the user
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

