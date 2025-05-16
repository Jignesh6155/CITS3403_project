from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import pytz
# --- Flask-Login integration ---
from flask_login import UserMixin
from flask_login import LoginManager

"""
Database models for the job application platform.

This module defines all SQLAlchemy ORM models, association tables, and relationships for users, job applications,
scraped jobs, resume analyses, friend requests, and notifications. It also includes Flask-Login integration for user sessions.
"""

db = SQLAlchemy()

# Association table for sharing job applications between users
application_shares = db.Table('application_shares',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('job_application_id', db.Integer, db.ForeignKey('job_application.id'), primary_key=True),
    db.Column('status', db.String(20), default='active')  # Status of the share (e.g., active, revoked)
)

# Association table for user friendships (self-referential many-to-many)
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """
    User account model.

    Attributes:
        id (int): Primary key.
        name (str): User's full name.
        email (str): Unique email address.
        password (str): Hashed password.
        job_applications (list[JobApplication]): Applications submitted by the user.
        job_searches (list[JobSearch]): Saved job searches.
        scraped_jobs (list[ScrapedJob]): Jobs scraped by the user.
        shared_applications (list[JobApplication]): Applications shared with other users.
        friends (list[User]): Friends of the user (self-referential many-to-many).
    """
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
    """
    Job application submitted by a user.

    Attributes:
        id (int): Primary key.
        title (str): Job title.
        company (str): Company name.
        location (str): Job location.
        job_type (str): Type of job (e.g., internship, full-time).
        closing_date (datetime): Application closing date.
        status (str): Application status (e.g., Applied, Interviewed).
        date_applied (datetime): Date the application was submitted.
        user_id (int): Foreign key to User.
        scraped_job_id (int): Foreign key to ScrapedJob.
        scraped_job (ScrapedJob): Relationship to the scraped job.
    """
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
    """
    Saved job search performed by a user.

    Attributes:
        id (int): Primary key.
        search_query (str): The search query string.
        results (str): JSON or text of search results.
        user_id (int): Foreign key to User.
    """
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255))
    results = db.Column(db.Text)  # JSON or text
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ScrapedJob(db.Model):
    """
    Job listing scraped from external sources (e.g., GradConnection).

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to User.
        title (str): Job title.
        posted_date (str): Date the job was posted.
        closing_in (str): Time until closing (e.g., '3 days').
        closing_date (datetime): Actual closing date (if parsed).
        ai_summary (str): AI-generated summary of the job.
        overview, responsibilities, requirements, skills_and_qualities, salary_info, about_company (str):
            JSON stringified lists of job details.
        full_text (str): Full job description text.
        link (str): URL to the job posting.
        source (str): Source of the job (e.g., 'GradConnection').
        tag_location, tag_jobtype, tag_category (str): Tagging fields for filtering/search.
    """
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
    """
    Analysis of a user's uploaded resume.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to User.
        filename (str): Name of the uploaded file.
        content_type (str): MIME type of the file.
        upload_date (datetime): Date the resume was uploaded.
        raw_text (str): Extracted text from the resume.
        keywords (str): JSON stringified list of extracted keywords.
        suggested_jobs (str): JSON stringified list of suggested job IDs.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255))
    content_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    raw_text = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON stringified list of extracted keywords
    suggested_jobs = db.Column(db.Text)  # JSON stringified list of job IDs

class FriendRequest(db.Model):
    """
    Friend request between two users.

    Attributes:
        id (int): Primary key.
        sender_id (int): Foreign key to User (sender).
        receiver_id (int): Foreign key to User (receiver).
        status (str): Status of the request (pending, accepted, rejected).
        created_at (datetime): When the request was created.
        updated_at (datetime): When the request was last updated.
        sender (User): Relationship to the sender.
        receiver (User): Relationship to the receiver.
    """
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
    """
    Notification for a user (e.g., friend request, job update).

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to User.
        content (str): Notification content.
        link (str): Optional link related to the notification.
        type (str): Notification type (e.g., 'friend_request').
        is_read (bool): Whether the notification has been read.
        created_at (datetime): When the notification was created.
        user (User): Relationship to the user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)  
    type = db.Column(db.String(50), nullable=False)  # e.g., 'friend_request', 'job_application_update', etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to the user
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

# --- Flask-Login user loader ---
# This function must be registered with the LoginManager instance in your app factory (see __init__.py)
# It tells Flask-Login how to load a user from a user ID stored in the session.
def load_user(user_id):
    """
    Flask-Login user loader callback.

    Args:
        user_id (int): The user ID stored in the session.

    Returns:
        User: The user object corresponding to the given ID, or None if not found.
    """
    from app import db
    return db.session.get(User, int(user_id))

