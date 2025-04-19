from flask import render_template, request
from app import app

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/resume")
def resume():
    return render_template("resume.html", active_page="resume")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html", active_page="analytics")

@app.route("/comms")
def comms():
    return render_template("comms.html", active_page="comms")

@app.route("/upload", methods=["POST"])
def upload():
    uploaded_file = request.files.get("resume")
    if uploaded_file:
        filename = uploaded_file.filename
        return render_template("resume.html", uploaded=True, filename=filename, active_page="resume")
    return render_template("resume.html", uploaded=False, active_page="resume")
