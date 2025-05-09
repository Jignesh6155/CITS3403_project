from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed, FileRequired

class AddApplicationForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    location = StringField('Location')
    job_type = SelectField('Job Type', choices=[
        ('', 'Select Type'),
        ('Internships', 'Internship'),
        ('Graduate-Jobs', 'Graduate Job'),
        ('Scholarships', 'Scholarship'),
        ('Clerkships', 'Clerkship')
    ])
    closing_date = DateField('Closing Date', format='%Y-%m-%d', validators=[], render_kw={"placeholder": "YYYY-MM-DD"})
    status = SelectField('Status', choices=[
        ('Saved', 'Saved'),
        ('Applied', 'Applied'),
        ('Screen', 'Screen'),
        ('Interviewing', 'Interviewing'),
        ('Offer', 'Offer'),
        ('Accepted', 'Accepted'),
        ('Archived', 'Archived'),
        ('Discontinued', 'Discontinued')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Application')

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class SigninForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResumeUploadForm(FlaskForm):
    resume = FileField('Resume', validators=[FileRequired(), FileAllowed(['pdf', 'doc', 'docx'], 'PDF, DOC, or DOCX only!')])
    submit = SubmitField('Upload Resume') 