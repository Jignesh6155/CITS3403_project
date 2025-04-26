from flask import render_template, request
from app import app

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

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