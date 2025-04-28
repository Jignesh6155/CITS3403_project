from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for sharing job applications between users
shared_applications = db.Table('shared_applications',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('job_application_id', db.Integer, db.ForeignKey('job_application.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Relationships
    job_applications = db.relationship('JobApplication', backref='owner', lazy=True)
    job_searches = db.relationship('JobSearch', backref='user', lazy=True)
    scraped_jobs = db.relationship('ScrapedJob', backref='user', lazy=True)
    shared_applications = db.relationship(
        'JobApplication',
        secondary=shared_applications,
        backref=db.backref('shared_with', lazy='dynamic')
    )

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    date_applied = db.Column(db.Date)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # shared_with handled by association table

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
