from flask import render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from app import app
from app.models import db, User
from app.models import ScrapedJob
import json
from app.utils.scraper_GC_jobs_detailed import get_jobs_full, save_jobs_to_db
from sqlalchemy import or_
import threading
import queue
import time
from app.utils.fuzzy_search import job_matches

# Global variables (for testing)
live_job_queue = queue.Queue()
HEADLESS_TOGGLE = True  # Set to False temporarily for debugging
SCRAPE_SIZE = 1

def background_scraper(user_id=1, jobtype='internships', discipline=None, location=None, keyword=None):
    print(f"[DEBUG] Starting scraping with: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
    with app.app_context():
        from app.utils.scraper_GC_jobs_detailed import get_jobs_full
        from app.models import db, ScrapedJob
        import json
        
        try:
            print(f"[DEBUG] Calling get_jobs_full with parameters: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
            jobs = get_jobs_full(jobtype=jobtype, discipline=discipline, location=location, keyword=keyword, max_pages=SCRAPE_SIZE, headless=HEADLESS_TOGGLE)
            print(f"[DEBUG] Successfully scraped {len(jobs)} jobs")
        except Exception as e:
            print(f"[ERROR] Error scraping jobs: {e}")
            import traceback
            traceback.print_exc()
            jobs = []
            
        for i, job in enumerate(jobs):
            try:
                # Save to DB
                print(f"[DEBUG] Saving job {i+1}/{len(jobs)} to database: {job.get('title')}")
                scraped_job = ScrapedJob(
                    user_id=user_id,
                    title=job.get("title"),
                    posted_date=job.get("posted_date"),
                    closing_in=job.get("closing_in"),
                    ai_summary=job.get("ai_summary"),
                    overview=json.dumps(job.get("overview", [])),
                    responsibilities=json.dumps(job.get("responsibilities", [])),
                    requirements=json.dumps(job.get("requirements", [])),
                    skills_and_qualities=json.dumps(job.get("skills_and_qualities", [])),
                    salary_info=json.dumps(job.get("salary_info", [])),
                    about_company=json.dumps(job.get("about_company", [])),
                    full_text=job.get("full_text"),
                    link=job.get("link"),
                    source="GradConnection"
                )
                db.session.add(scraped_job)
                db.session.commit()
                print(f"[DEBUG] Successfully saved job to database: {job.get('title')}")
                
                # Push to live queue
                about = job.get("about_company", [])
                live_job_queue.put({
                    'title': job.get("title"),
                    'company': about[0] if about else '',
                    'posted_date': job.get("posted_date"),
                    'closing_in': job.get("closing_in"),
                    'ai_summary': job.get("ai_summary"),
                    'link': job.get("link"),
                })
                print(f"[DEBUG] Added job to live queue: {job.get('title')}")
            except Exception as e:
                print(f"[ERROR] Error saving job to DB: {e}")
                db.session.rollback()
                import traceback
                traceback.print_exc()
            
            time.sleep(0.1)
            
        # Send completion message to notify frontend that scraping is complete
        live_job_queue.put({
            'status': 'complete'
        })
        print(f"[DEBUG] Scraping complete, sent completion message to queue")

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


@app.route("/job-search")
def job_search():
    scraped_jobs = ScrapedJob.query.all()
    for job in scraped_jobs:
        try:
            job.about_company_parsed = json.loads(job.about_company) if job.about_company else None
        except Exception:
            job.about_company_parsed = None
        job.company = job.about_company_parsed[0] if job.about_company_parsed and len(job.about_company_parsed) > 0 else ""
    return render_template("jobSearch.html", active_page="job-search", scraped_jobs=scraped_jobs)

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
        return render_template("jobSearch.html", uploaded=True, filename=f.filename, active_page="job-search")
    return render_template("jobSearch.html", uploaded=False, active_page="job-search")

@app.route("/job-tracker")
def job_tracker():
    return render_template("jobtracker.html", active_page="job-tracker")

@app.route("/api/scraped-jobs")
def api_scraped_jobs():
    # Get query params
    search = request.args.get('search', '').strip().lower()
    location = request.args.get('location', '').strip().lower()
    job_type = request.args.get('type', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))

    # Query all jobs
    jobs_query = ScrapedJob.query
    jobs = jobs_query.all()

    filtered = [job for job in jobs if job_matches(job, search, location, job_type, category)]
    total = len(filtered)
    paginated = filtered[offset:offset+limit]
    result = []
    for job in paginated:
        try:
            about = json.loads(job.about_company) if job.about_company else []
        except Exception:
            about = []
        result.append({
            'title': job.title,
            'company': about[0] if about else '',
            'posted_date': job.posted_date,
            'closing_in': job.closing_in,
            'ai_summary': job.ai_summary,
            'link': job.link,
        })
    return jsonify({
        'jobs': result,
        'has_more': offset+limit < total
    })

@app.route('/api/start-scraping', methods=['POST'])
def api_start_scraping():
    try:
        user = User.query.first()
        data = request.get_json(force=True) or {}
        print("[DEBUG] Received scraping parameters:", data)
        
        jobtype = data.get('jobtype', 'internships')
        discipline = data.get('discipline') or None
        location = data.get('location') or None
        keyword = data.get('keyword') or None
        
        print(f"[DEBUG] Starting background scraper thread with parameters: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
        threading.Thread(target=background_scraper, args=(user.id if user else 1, jobtype, discipline, location, keyword), daemon=True).start()
        print("[DEBUG] Background scraper thread started")
        return '', 202
    except Exception as e:
        print(f"[ERROR] Error in /api/start-scraping endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping-stream')
def api_scraping_stream():
    def event_stream():
        while True:
            try:
                # Use a 30-second timeout to prevent the connection from blocking forever
                job = live_job_queue.get(timeout=30)
                yield f"data: {json.dumps(job)}\n\n"
                
                # If this was the completion message, we're done
                if job.get('status') == 'complete':
                    break
            except queue.Empty:
                # Send a ping event every 30 seconds to keep the connection alive
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

