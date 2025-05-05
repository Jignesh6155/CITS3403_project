from flask import render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from app import app
from app.models import db, User, JobApplication, FriendRequest
from app.models import ScrapedJob
import json
from app.utils.scraper_GC_jobs_detailed import get_jobs_full, save_jobs_to_db
from sqlalchemy import or_
import threading
import queue
import time
from app.utils.fuzzy_search import job_matches
from app.utils import resume_processor
import datetime
# Add after existing imports
from datetime import datetime, timedelta

# Simple in-memory rate limiting
request_counts = {}

def rate_limit_check(user_id, action, max_requests=5, window_seconds=3600):
    """Basic rate limiting"""
    key = f"{user_id}:{action}"
    now = datetime.utcnow()
    
    if key not in request_counts:
        request_counts[key] = []
    
    # Clean old requests
    request_counts[key] = [t for t in request_counts[key] 
                           if t > now - timedelta(seconds=window_seconds)]
    
    # Check if over limit
    if len(request_counts[key]) >= max_requests:
        return False
    
    # Add current request
    request_counts[key].append(now)
    return True

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
    if 'name' not in session:
        return redirect(url_for("home"))
    user = User.query.filter_by(name=session["name"]).first()
    if not user:
        return redirect(url_for("home"))
    applications = JobApplication.query.filter_by(owner=user).all()
    all_statuses = ["Saved", "Applied", "Screen", "Interviewing", "Offer", "Accepted", "Archived", "Discontinued"]
    status_counts_dict = {status: 0 for status in all_statuses}
    company_counts = {}
    last_applied_raw = None
    for app in applications:
        if app.status in status_counts_dict:
            status_counts_dict[app.status] += 1
        if app.date_applied:
            if not last_applied_raw or app.date_applied > last_applied_raw:
                last_applied_raw = app.date_applied
    last_applied = last_applied_raw.strftime("%Y-%m-%d") if last_applied_raw else "N/A"
    status_labels = []
    status_counts = []
    for status, count in status_counts_dict.items():
        if count > 0:
            status_labels.append(status)
            status_counts.append(count)
    status_summary = list(zip(status_labels, status_counts))
    applied = status_counts_dict["Applied"]
    saved = status_counts_dict["Saved"]
    interviewing = status_counts_dict["Interviewing"]
    offers = status_counts_dict["Offer"]
    in_progress = sum(status_counts_dict[s] for s in all_statuses if s not in ["Accepted", "Archived", "Discontinued"])
    inactive_statuses = {"Accepted", "Archived", "Discontinued"}
    active_applications = [app for app in applications if app.status not in inactive_statuses]
    active_count = len(active_applications)
    achievements = []
    if applied >= 1:
        achievements.append(("First Application Sent", "You're on your way!", "green"))
    if interviewing >= 1:
        achievements.append(("First Interview!", "Nailed the first impression!", "blue"))
    if offers >= 1:
        achievements.append(("Offer Received", "You got the bag!", "yellow"))
    if applied >= 10:
        achievements.append(("Application Hustler", "10+ applications sent!", "purple"))
    if offers >= 3:
        achievements.append(("Multi-Offer Champ", "3+ offers received!", "orange"))
    if interviewing >= 5:
        achievements.append(("Interview Veteran", "5 interviews done!", "blue"))
    if saved >= 5:
        achievements.append(("Job Curator", "Saved 5 jobs to consider!", "cyan"))
    if saved >= 15:
        achievements.append(("Opportunity Hoarder", "15 jobs saved!", "pink"))
    if in_progress >= 10:
        achievements.append(("On the Grind", "10 ongoing applications!", "lime"))
    if status_counts_dict["Archived"] >= 1:
        achievements.append(("Archived Veteran", "At least 1 role archived.", "gray"))
    if status_counts_dict["Accepted"] >= 1:
        achievements.append(("You're Hired!", "Accepted an offer!", "emerald"))
    if status_counts_dict["Discontinued"] >= 1:
        achievements.append(("No Longer Pursuing", "Moved on from a role.", "rose"))
    badges_earned = len(achievements)
    return render_template("dashboard.html",
        name=user.name,
        in_progress=in_progress,
        interviews=interviewing,
        applied=applied,
        saved=saved,
        offers=offers,
        last_applied=last_applied,
        status_labels=status_labels,
        status_counts=status_counts,
        status_summary=status_summary,
        active_count=active_count,
        badges_earned=badges_earned,
        achievements=achievements
    )
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
    resume_keywords = session.pop('resume_keywords', [])
    suggested_jobs = session.pop('suggested_jobs', [])
    return render_template("jobSearch.html", active_page="job-search", scraped_jobs=scraped_jobs, resume_keywords=resume_keywords, suggested_jobs=suggested_jobs)
@app.route("/analytics")
def analytics():
    return render_template("analytics.html", active_page="analytics")
@app.route("/comms")
def comms():
    if 'name' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(name=session['name']).first()

    # ✅ Get all JobApplications where the current user is in shared_with
    shared_apps = JobApplication.query \
        .filter(JobApplication.shared_with.any(id=user.id)) \
        .all()
    
    # Get pending friend requests
    pending_requests = FriendRequest.query.filter_by(
        receiver_id=user.id, status='pending'
    ).all()

    return render_template(
        "comms.html",
        active_page="comms",
        current_user=user,
        shared_apps=shared_apps,
        pending_requests=pending_requests,
        chart_data={}
    )
@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("resume")
    if f and f.filename:
        print("[DEBUG] Processing uploaded resume with AI")
        filename = f.filename
        content_type = f.content_type or f.mimetype or ''
        file_bytes = f.read()
        text = resume_processor.extract_text(file_bytes, content_type)
        # Get AI-suggested job titles (keywords)
        job_titles = resume_processor.extract_keywords_openai(text)
        print("[DEBUG] Extracted keywords:", job_titles)
        # Find up to 5 jobs that fuzzy match any keyword
        from app.models import ScrapedJob
        import json
        all_jobs = ScrapedJob.query.all()
        print("[DEBUG] Number of jobs in DB:", len(all_jobs))
        suggestions = []
        for job in all_jobs:
            for keyword in job_titles:
                if job_matches(job, search=keyword, location='', job_type='', category='', confidence=0.35):
                    print("[DEBUG] Found job that matches keyword:", job.title)
                    try:
                        about = json.loads(job.about_company) if job.about_company else []
                    except Exception:
                        about = []
                    suggestions.append({
                        'title': job.title,
                        'company': about[0] if about else '',
                        'posted_date': job.posted_date,
                        'closing_in': job.closing_in,
                        'link': job.link,
                    })
                    break  # Only add each job once
            if len(suggestions) >= 5:
                break
        session['resume_keywords'] = job_titles
        session['suggested_jobs'] = suggestions
        return redirect(url_for('job_search'))
    # If no file, clear session and redirect
    session['resume_keywords'] = []
    session['suggested_jobs'] = []
    return redirect(url_for('job_search'))
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
@app.route('/send-friend-request', methods=['POST'])
def send_friend_request():
    if 'name' not in session:
        return redirect(url_for('home'))
    
    email = request.form.get('email')
    if email:
        current_user = User.query.filter_by(name=session['name']).first()
        
        # Rate limiting
        if not rate_limit_check(current_user.id, 'friend_request', max_requests=10, window_seconds=3600):
            flash('You have sent too many friend requests. Please try again later.', 'error')
            return redirect(url_for('comms'))
            
        friend = User.query.filter_by(email=email).first()
        
        if not friend:
            flash('User not found', 'error')
            return redirect(url_for('comms'))
            
        if friend.id == current_user.id:
            flash('You cannot send a friend request to yourself', 'error')
            return redirect(url_for('comms'))
            
        # Check if already friends
        if friend in current_user.friends:
            flash('You are already friends with this user', 'error')
            return redirect(url_for('comms'))
            
        # Check if request already exists
        existing_request = FriendRequest.query.filter_by(
            sender_id=current_user.id, receiver_id=friend.id, status='pending'
        ).first()
        
        if existing_request:
            flash('Friend request already sent', 'error')
            return redirect(url_for('comms'))
            
        # Check if there's a request from the other user
        existing_reverse_request = FriendRequest.query.filter_by(
            sender_id=friend.id, receiver_id=current_user.id, status='pending'
        ).first()
        
        if existing_reverse_request:
            # Auto-accept the other request
            existing_reverse_request.status = 'accepted'
            # Ensure bidirectional friendship
            current_user.friends.append(friend)
            friend.friends.append(current_user)
            db.session.commit()
            flash(f'You are now friends with {friend.name}', 'success')
            return redirect(url_for('comms'))
        
        # Create a new request
        new_request = FriendRequest(
            sender_id=current_user.id,
            receiver_id=friend.id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        
        flash('Friend request sent', 'success')
    else:
        flash('Please enter an email', 'error')
        
    return redirect(url_for('comms'))
@app.route('/handle-friend-request/<int:request_id>', methods=['POST'])
def handle_friend_request(request_id):
    if 'name' not in session:
        return redirect(url_for('home'))
        
    current_user = User.query.filter_by(name=session['name']).first()
    friend_request = FriendRequest.query.get(request_id)
    
    # Security checks
    if not friend_request or friend_request.receiver_id != current_user.id:
        flash('Invalid request', 'error')
        return redirect(url_for('comms'))
        
    action = request.form.get('action')
    
    if action == 'accept':
        friend_request.status = 'accepted'
        # Add to friends (both ways)
        sender = User.query.get(friend_request.sender_id)
        
        # Ensure bidirectional friendship
        current_user.friends.append(sender)
        sender.friends.append(current_user)
        
        db.session.commit()
        flash(f'You are now friends with {sender.name}', 'success')
    elif action == 'reject':
        friend_request.status = 'rejected'
        db.session.commit()
        flash('Friend request rejected', 'success')
    
    return redirect(url_for('comms'))
@app.route("/add-application", methods=["POST"])
def add_application():
    if 'name' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return redirect(url_for('home'))
    company = request.form.get("company")
    title = request.form.get("title")
    date_applied = request.form.get("date_applied")
    status = request.form.get("status")
    application = JobApplication(
        company=company,
        title=title,
        status=status,
        date_applied=datetime.datetime.strptime(date_applied, "%Y-%m-%d"),
        owner=user
    )
    db.session.add(application)
    db.session.commit()
    return redirect(url_for("job_tracker"))

@app.route('/share-application/<int:app_id>', methods=['POST'])
def share_application(app_id):
    if 'name' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(name=session['name']).first()
    application = JobApplication.query.get(app_id)

    if not application or application.owner_id != user.id:
        flash('Application not found or you do not own this application', 'error')
        return redirect(url_for('job_tracker'))

    friend_id = request.form.get('friend_id')
    friend = User.query.get(friend_id)

    if friend and friend in user.friends:
        if application not in friend.shared_applications:
            friend.shared_applications.append(application)
            db.session.commit()
            flash(f'Application shared with {friend.name}', 'success')
        else:
            flash('Application already shared with this friend', 'error')
    else:
        flash('Friend not found', 'error')

    return redirect(url_for('job_tracker'))

@app.route("/update-job-status", methods=["POST"])
def update_job_status():
    job_id = request.json.get("job_id")
    new_status = request.json.get("new_status")
    job = JobApplication.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    job.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated"})
@app.route('/job-tracker')
def job_tracker():
    if 'name' not in session:
        return redirect(url_for('home'))
    
    user = User.query.filter_by(name=session['name']).first()

    # 🚫 Only applications OWNED by the current user
    applications = JobApplication.query.filter_by(owner_id=user.id).all()

    statuses = ["Saved", "Applied", "Screen", "Interviewing", "Offer", "Accepted", "Archived", "Discontinued"]
    grouped = {status: [] for status in statuses}

    for app in applications:
        grouped[app.status].append(app)

    return render_template(
        "jobtracker.html",
        active_page="job-tracker",
        grouped=grouped,
        current_user=user
    )