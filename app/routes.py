from flask import render_template, request, redirect, url_for, session
from app import app
from app.models import db, User

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    if name and email and password:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("index.html", error="Email already registered.")
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["name"] = name
        return redirect(url_for("dashboard"))
    return render_template("index.html", error="All fields are required.")

@app.route("/signin", methods=["POST"])
def signin():
    email = request.form.get("email")
    password = request.form.get("password")

    if email and password:
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["name"] = user.name
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="Invalid Email or Password.")
    return render_template("index.html", error="All fields are required.")

@app.route("/dashboard")
def dashboard():
    name = session.get("name", "User")
    return render_template("dashboard.html", name=name)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/resume-analysis")
def resume_analysis():
    return render_template("resume.html", active_page="resume-analysis")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html", active_page="analytics")

@app.route("/comms")
def comms():
    return render_template("comms.html", active_page="comms")

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("resume")
    if f:
        return render_template("resume.html", uploaded=True, filename=f.filename, active_page="resume-analysis")
    return render_template("resume.html", uploaded=False, active_page="resume-analysis")

@app.route("/job-tracker")
def job_tracker():
    return render_template("jobtracker.html", active_page="job-tracker")

