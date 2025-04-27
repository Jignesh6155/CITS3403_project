from flask import render_template, request, redirect, url_for, session
from app import app

app.secret_key = "your_secret_key"  # Required for session handling

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    if name:
        session["name"] = name  # Store the name in the session
        return redirect(url_for("dashboard"))
    return render_template("index.html", error="Name is required")

@app.route("/dashboard")
def dashboard():
    name = session.get("name", "User")  # Default to "User" if no name in session
    return render_template("dashboard.html", active_page="dashboard", name=name)

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

@app.route("/logout")
def logout():
    session.clear()  # Clear the session
    return redirect(url_for("home"))  # Redirect to the sign-up page