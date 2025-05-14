"""
Routes for the main blueprint of the application.
All routes are registered under the 'main_bp' Blueprint.
IMPORTANT: Do NOT use @app.route. Use @main_bp.route for all routes in this file.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from app.models import db, User, JobApplication, FriendRequest, Notification
from app.models import ScrapedJob, application_shares
from collections import Counter
import json
from app.utils.scraper_GC_jobs_detailed import get_jobs_full, save_jobs_to_db
from sqlalchemy import or_, asc
from sqlalchemy import text
import threading
import queue
import time
from app.utils.fuzzy_search import job_matches
from app.utils import resume_processor
import string
from datetime import datetime, timedelta, timezone
import pytz
import re
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing
from flask import current_app


# Simple in-memory rate limiting
request_counts = {}
def rate_limit_check(user_id, action, max_requests=5, window_seconds=3600):
    """Basic rate limiting"""
    key = f"{user_id}:{action}"
    now = datetime.now(timezone.utc)
    
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
def create_notification(user_id, content, link=None, notification_type="general"):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        content=content,
        link=link,
        type=notification_type,
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    return notification
# Global variables (for testing)
live_job_queue = queue.Queue()
HEADLESS_TOGGLE = False  # Set to False temporarily for debugging
SCRAPE_SIZE = 3
def background_scraper(user_id=1, jobtype='internships', discipline=None, location=None, keyword=None):
    if current_app.config.get('DEBUG', False):
        print(f"[DEBUG] Starting scraping with: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
    with current_app.app_context():
        from app.utils.scraper_GC_jobs_detailed import get_jobs_full
        from app.models import db, ScrapedJob
        import json
        from datetime import datetime, timedelta
        import pytz
        import re
        
        try:
            if current_app.config.get('DEBUG', False):
                print(f"[DEBUG] Calling get_jobs_full with parameters: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
            jobs = get_jobs_full(jobtype=jobtype, discipline=discipline, location=location, keyword=keyword, max_pages=SCRAPE_SIZE, headless=HEADLESS_TOGGLE)
            if current_app.config.get('DEBUG', False):
                print(f"[DEBUG] Successfully scraped {len(jobs)} jobs")
            
            # Clear existing jobs for this search
            ScrapedJob.query.filter_by(
                user_id=user_id,
                tag_jobtype=jobtype,
                tag_location=location,
                tag_category=discipline
            ).delete()
            db.session.commit()
            
            perth_tz = pytz.timezone('Australia/Perth')
            
            for i, job in enumerate(jobs):
                try:
                    closing_in = job.get("closing_in", "")
                    closing_date = None
                    # Estimate closing_date from closing_in
                    if closing_in:
                        closing_in_lower = closing_in.lower()
                        now = datetime.now(timezone.utc)
                        days_match = re.search(r'(\d+)\s*days?', closing_in_lower)
                        months_match = re.search(r'(\d+)\s*months?', closing_in_lower)
                        hours_match = re.search(r'(\d+)\s*hours?', closing_in_lower)
                        if 'an hour' in closing_in_lower:
                            closing_date = now  # Same day
                            closing_in = "Closing in 1 hour"
                        elif hours_match:
                            closing_date = now  # Same day
                            hours = int(hours_match.group(1))
                            closing_in = f"Closing in {hours} hours"
                        elif 'a day' in closing_in_lower:
                            closing_date = now + timedelta(days=1)
                            closing_in = "Closing in 1 day"
                        elif days_match:
                            days = int(days_match.group(1))
                            closing_date = now + timedelta(days=days)
                            closing_in = f"Closing in {days} days"
                        elif 'a month' in closing_in_lower:
                            closing_date = now + timedelta(days=30)
                            closing_in = "Closing in 1 month"
                        elif months_match:
                            months = int(months_match.group(1))
                            closing_date = now + timedelta(days=30*months)
                            closing_in = f"Closing in {months} months"
                        elif closing_in_lower.strip() == 'n/a':
                            closing_date = None  # No estimate possible
                        else:
                            closing_date = None  # Unknown format, leave as None
                    
                    # Save to DB
                    if current_app.config.get('DEBUG', False):
                        print(f"[DEBUG] Saving job {i+1}/{len(jobs)} to database: {job.get('title')}")
                    scraped_job = ScrapedJob(
                        user_id=user_id,
                        title=job.get("title"),
                        posted_date=job.get("posted_date"),
                        closing_in=closing_in,
                        closing_date=closing_date,
                        ai_summary=job.get("ai_summary"),
                        overview=json.dumps(job.get("overview", [])),
                        responsibilities=json.dumps(job.get("responsibilities", [])),
                        requirements=json.dumps(job.get("requirements", [])),
                        skills_and_qualities=json.dumps(job.get("skills_and_qualities", [])),
                        salary_info=json.dumps(job.get("salary_info", [])),
                        about_company=json.dumps(job.get("about_company", [])),
                        full_text=job.get("full_text"),
                        link=job.get("link"),
                        source="GradConnection",
                        tag_location=location,
                        tag_jobtype=jobtype,   
                        tag_category=discipline
                    )
                    db.session.add(scraped_job)
                    db.session.commit()
                    if current_app.config.get('DEBUG', False):
                        print(f"[DEBUG] Successfully saved job to database: {job.get('title')}")
                    
                    # Push to live queue with tags
                    about = job.get("about_company", [])
                    live_job_queue.put({
                        'title': job.get("title"),
                        'company': about[0] if about else '',
                        'posted_date': job.get("posted_date"),
                        'closing_in': closing_in,
                        'closing_date': closing_date.strftime("%d %b %Y") if closing_date else None,
                        'ai_summary': job.get("ai_summary"),
                        'link': job.get("link"),
                        'tag_location': location,
                        'tag_jobtype': jobtype,
                        'tag_category': discipline
                    })
                    if current_app.config.get('DEBUG', False):
                        print(f"[DEBUG] Added job to live queue: {job.get('title')}")
                except Exception as e:
                    if current_app.config.get('DEBUG', False):
                        print(f"[ERROR] Error saving job to DB: {e}")
                    db.session.rollback()
                    import traceback
                    traceback.print_exc()
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"[ERROR] Error in background scraper: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Always send completion message
            live_job_queue.put({
                'status': 'complete'
            })
            if current_app.config.get('DEBUG', False):
                print(f"[DEBUG] Scraping complete, sent completion message to queue")
def job_matches(job, search, location, job_type, category, confidence=0.35):
    """Check if a job matches the search criteria"""
    if not job:
        return False
        
    # If no filters are applied, return all jobs
    if not any([search, location, job_type, category]):
        return True
        
    # Convert all search terms to lowercase for case-insensitive matching
    search = search.lower()
    location = location.lower()
    job_type = job_type.lower()
    category = category.lower()
    
    # Basic text search in title and full text
    basic_match = (
        (not search or 
         search in job.title.lower() or 
         (job.full_text and search in job.full_text.lower())
        )
    )
    
    # Tag-based filtering
    location_match = (
        not location or 
        (job.tag_location and location in job.tag_location.lower())
    )
    
    job_type_match = (
        not job_type or 
        (job.tag_jobtype and job_type in job.tag_jobtype.lower())
    )
    
    category_match = (
        not category or 
        (job.tag_category and category in job.tag_category.lower())
    )
    
    return basic_match and location_match and job_type_match and category_match

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    return render_template("index.html")

@main_bp.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    if name and email and password:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("index.html", error="Email already registered.")
        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("main.dashboard"))
    return render_template("index.html", error="All fields are required.")

@main_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        # Render the login page for GET requests (Flask-Login redirects here if not authenticated)
        return render_template("index.html")  # Change to your login template if different
    # POST: handle login form submission
    email = request.form.get("email")
    password = request.form.get("password")
    if email and password:
        user = User.query.filter_by(email=email).first()
        # Check the password hash
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            return render_template("index.html", error="Invalid Email or Password.")
    return render_template("index.html", error="All fields are required.")

@main_bp.route("/dashboard")
@login_required  # Require login for dashboard
def dashboard():
    user = current_user
    applications = JobApplication.query.filter_by(user=user).all()
    all_statuses = ["Saved", "Applied", "Screen", "Interviewing", "Offer", "Accepted", "Archived", "Discontinued"]
    status_counts_dict = {status: 0 for status in all_statuses}
    last_applied_raw = None
    for app in applications:
        if app.status in status_counts_dict:
            status_counts_dict[app.status] += 1
        if app.date_applied and (not last_applied_raw or app.date_applied > last_applied_raw):
            last_applied_raw = app.date_applied
    last_applied = last_applied_raw.strftime("%Y-%m-%d") if last_applied_raw else "N/A"
    status_labels = [status for status, count in status_counts_dict.items() if count > 0]
    status_counts = [count for status, count in status_counts_dict.items() if count > 0]
    status_summary = list(zip(status_labels, status_counts))
    applied = status_counts_dict["Applied"]
    saved = status_counts_dict["Saved"]
    interviewing = status_counts_dict["Interviewing"]
    offers = status_counts_dict["Offer"]
    in_progress = sum(status_counts_dict[s] for s in all_statuses if s not in ["Accepted", "Archived", "Discontinued"])
    active_applications = [app for app in applications if app.status not in {"Accepted", "Archived", "Discontinued"}]
    active_count = len(active_applications)
    # Achievements
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
    # New Sneak Peek Data
    random_jobs = ScrapedJob.query.order_by(db.func.random()).limit(3).all()
    total_apps = len(applications)
    success_rate = round((offers / total_apps) * 100, 1) if total_apps else 0
    friends = user.friends.all()
    all_users = [user] + friends
    leaderboard = sorted(
        [{'name': u.name, 'apps_count': len(u.job_applications)} for u in all_users],
        key=lambda x: x['apps_count'],
        reverse=True
    )[:3]
    # Retrieve suggested_jobs from session for the sneak peek
    suggested_jobs = session.get('suggested_jobs', [])
    if not suggested_jobs:
        # Query the 5 soonest closing jobs (with a closing_date)
        soonest_jobs = ScrapedJob.query.filter(ScrapedJob.closing_date != None).order_by(asc(ScrapedJob.closing_date)).limit(5).all()
        suggested_jobs = []
        for job in soonest_jobs:
            try:
                about = json.loads(job.about_company) if job.about_company else []
            except Exception:
                about = []
            suggested_jobs.append({
                'title': job.title,
                'company': about[0] if about else '',
                'closing_in': job.closing_in,
                'closing_date': job.closing_date.strftime('%Y-%m-%d') if job.closing_date else '',
                'link': job.link,
                'ai_summary': getattr(job, 'ai_summary', ''),
                'tags': {
                    'location': job.tag_location,
                    'jobtype': job.tag_jobtype,
                    'category': job.tag_category
                }
            })
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
        achievements=achievements,
        random_jobs=random_jobs,
        total_apps=total_apps,
        success_rate=success_rate,
        leaderboard_preview=leaderboard,
        suggested_jobs=suggested_jobs,
        user=user
    )

@main_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))

@main_bp.route("/job-search")
@login_required  # Require login for job search
def job_search():
    user = current_user
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

@main_bp.route("/analytics")
@login_required  # Require login for analytics
def analytics():
    user = current_user
    # --- grab all of this user's applications ----------------------------
    applications = JobApplication.query.filter_by(user=user).all()
    total_apps   = len(applications)
    # quick counters -------------------------------------------------------
    interviews  = sum(a.status == "Interviewing" for a in applications)
    offers      = sum(a.status == "Offer"         for a in applications)
    rejections  = sum(a.status in ("Archived", "Discontinued") for a in applications)
    # avg response time (days) -------------------------------------------
    responded = [
        a for a in applications
        if a.status in ("Offer", "Accepted", "Archived", "Discontinued")
        and a.date_applied and a.closing_date
    ]
    avg_resp_days = (
        round(sum((a.closing_date - a.date_applied).days for a in responded) /
              len(responded), 1)
        if responded else None
    )
    success_rate = round((offers / total_apps) * 100, 1) if total_apps else 0
    # status / type distributions ----------------------------------------
    status_counts, type_counts = {}, {}
    for a in applications:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
        t = a.job_type or "Unknown"
        type_counts[t] = type_counts.get(t, 0) + 1
    # weekly snapshot (last 7 days) --------------------------------------
    today = datetime.now(pytz.timezone("Australia/Perth")).date()
    weekly_labels, weekly_apps, weekly_int, weekly_off = [], [], [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        weekly_labels.append(day.strftime("%a"))
        weekly_apps.append(sum(a.date_applied
                               and a.date_applied.date() == day
                               for a in applications))
        weekly_int.append(sum(a.status == "Interviewing"
                              and a.date_applied
                              and a.date_applied.date() == day
                              for a in applications))
        weekly_off.append(sum(a.status == "Offer"
                              and a.date_applied
                              and a.date_applied.date() == day
                              for a in applications))
    # cumulative applications over calendar time -------------------------
    by_day = Counter(a.date_applied.date()
                     for a in applications if a.date_applied)
    cum_labels, cum_counts, running = [], [], 0
    for d in sorted(by_day):
        running += by_day[d]
        cum_labels.append(d.strftime("%d %b"))
        cum_counts.append(running)
    # --------------------------------------------------------------------
    return render_template(
        "analytics.html",
        active_page="analytics",
        # tiles
        total_apps   = total_apps,
        interviews   = interviews,
        offers       = offers,
        avg_response = avg_resp_days,
        success_rate = success_rate,
        # weekly
        weekly_labels = weekly_labels,
        weekly_apps   = weekly_apps,
        weekly_int    = weekly_int,
        weekly_off    = weekly_off,
        # outcomes / breakdowns
        outcome_labels = ["Offers", "Rejections"],
        outcome_counts = [offers, rejections],
        type_labels    = list(type_counts.keys()),
        type_counts    = list(type_counts.values()),
        status_labels  = list(status_counts.keys()),
        status_counts  = list(status_counts.values()),
        # cumulative
        cum_labels  = cum_labels,
        cum_counts  = cum_counts,
    )

@main_bp.route('/toggle-favorite/<int:friend_id>', methods=['POST'])
def toggle_favorite(friend_id):
    print(f"Toggle favorite request received for friend_id: {friend_id}")
    
    if 'name' not in session:
        print("Error: Not logged in")
        return jsonify({"error": "Not logged in"}), 401
        
    current_user = User.query.filter_by(name=session['name']).first()
    if not current_user:
        print("Error: User not found")
        return jsonify({"error": "User not found"}), 404
        
    friend = User.query.get(friend_id)
    if not friend:
        print(f"Error: Friend with ID {friend_id} not found")
        return jsonify({"error": "Friend not found"}), 404
        
    # Check if this is actually a friend
    if friend not in current_user.friends:
        print(f"Error: User {current_user.id} is not friends with {friend_id}")
        return jsonify({"error": "Not friends with this user"}), 403
    
    try:
        # For this implementation, we'll use localStorage on the client side 
        # to track favorites, so we don't need to modify the database.
        print(f"Toggle favorite successful for friend_id: {friend_id}")
        
        return jsonify({
            "success": True, 
            "is_favorite": True
        })
        
    except Exception as e:
        print(f"Error in toggle_favorite: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_bp.route("/comms")
@login_required  # Require login for friends/comms
def comms():
    user = current_user
    # Get all JobApplications where the current user is in shared_with
    shared_apps = JobApplication.query \
        .filter(JobApplication.shared_with.any(id=user.id)) \
        .all()
    
    # Get app statuses using raw SQL with proper text() wrapper
    app_statuses = {}
    for app in shared_apps:
        result = db.session.execute(
            text("SELECT status FROM application_shares WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": user.id, "app_id": app.id}
        ).fetchone()
        
        # Default to 'active' if no status found
        status = result[0] if result else 'active'
        app_statuses[app.id] = status
    
    # Get pending friend requests
    pending_requests = FriendRequest.query.filter_by(
        receiver_id=user.id, status='pending'
    ).all()
    
    # Get the current user's friends
    user_friends = user.friends.all()
    
    # Get friend request records for "recent" sorting
    friend_requests = {}
    for friend in user_friends:
        request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == friend.id)) |
            ((FriendRequest.sender_id == friend.id) & (FriendRequest.receiver_id == user.id))
        ).order_by(FriendRequest.updated_at.desc()).first()
        
        if request:
            friend_requests[friend.id] = request
    
    # Count shared apps per friend
    shared_apps_count = {}
    for friend in user_friends:
        count = JobApplication.query.filter_by(user_id=friend.id) \
            .filter(JobApplication.shared_with.any(id=user.id)) \
            .count()
        shared_apps_count[friend.id] = count
    
    return render_template(
        "comms.html",
        active_page="comms",
        user=user,
        current_user=user,
        shared_apps=shared_apps,
        app_statuses=app_statuses,
        pending_requests=pending_requests,
        friend_requests=friend_requests,  # Pass friend requests for sorting by recent
        shared_apps_count=shared_apps_count  # Pass shared apps count for sorting
    )

@main_bp.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("resume")
    if f and f.filename:
        if current_app.config.get('DEBUG', False):
            print("[DEBUG] Processing uploaded resume with AI")
        filename = f.filename
        content_type = f.content_type or f.mimetype or ''
        file_bytes = f.read()
        text = resume_processor.extract_text(file_bytes, content_type)
        # Get AI-suggested job titles (keywords)
        job_titles = resume_processor.extract_keywords_openai(text)
        job_titles = [kw.strip().strip(string.punctuation) for kw in job_titles if kw.strip()]
        if current_app.config.get('DEBUG', False):
            print("[DEBUG] Extracted keywords:", job_titles)
        # Find up to 5 jobs that fuzzy match any keyword
        from app.models import ScrapedJob
        import json
        all_jobs = ScrapedJob.query.all()
        if current_app.config.get('DEBUG', False):
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
            if len(suggestions) >= 20:
                break
        session['resume_keywords'] = job_titles
        session['suggested_jobs'] = suggestions
        return redirect(url_for('main.job_search'))
    # If no file, clear session and redirect
    session['resume_keywords'] = []
    session['suggested_jobs'] = []
    return redirect(url_for('main.job_search'))

@main_bp.route("/api/scraped-jobs")
def api_scraped_jobs():
    try:
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
                
            # Format closing date if it exists
            closing_date_str = None
            if job.closing_date:
                closing_date_str = job.closing_date.strftime("%d %b %Y")  # e.g., "14 Feb 2025"
                
            # Format tags for display
            tags = {
                'location': job.tag_location if job.tag_location else None,
                'jobtype': job.tag_jobtype if job.tag_jobtype else None,
                'category': job.tag_category if job.tag_category else None
            }
            
            result.append({
                'title': job.title,
                'company': about[0] if about else '',
                'posted_date': job.posted_date,
                'closing_in': job.closing_in,
                'closing_date': closing_date_str,
                'ai_summary': job.ai_summary,
                'link': job.link,
                'tags': tags
            })
            
        return jsonify({
            'jobs': result,
            'has_more': offset+limit < total,
            'total': total
        })
    except Exception as e:
        print(f"[ERROR] Error in /api/scraped-jobs endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/start-scraping', methods=['POST'])
def api_start_scraping():
    try:
        if 'name' not in session:
            return jsonify({"error": "Not logged in"}), 401
            
        user = User.query.filter_by(name=session['name']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        data = request.get_json(force=True) or {}
        if current_app.config.get('DEBUG', False):
            print("[DEBUG] Received scraping parameters:", data)
        
        jobtype = data.get('jobtype', 'internships')
        discipline = data.get('discipline') or None
        location = data.get('location') or None
        keyword = data.get('keyword') or None
        
        # Rate limit check
        if not rate_limit_check(user.id, 'scraping'):
            return jsonify({"error": "Rate limit exceeded. Please wait before starting another search."}), 429
        
        if current_app.config.get('DEBUG', False):
            print(f"[DEBUG] Starting background scraper thread with parameters: jobtype={jobtype}, discipline={discipline}, location={location}, keyword={keyword}")
        threading.Thread(target=background_scraper, args=(user.id, jobtype, discipline, location, keyword), daemon=True).start()
        if current_app.config.get('DEBUG', False):
            print("[DEBUG] Background scraper thread started")
        return '', 202
    except Exception as e:
        print(f"[ERROR] Error in /api/start-scraping endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/scraping-stream')
def api_scraping_stream():
    if 'name' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    def event_stream():
        while True:
            try:
                # Use a 30-second timeout to prevent the connection from blocking forever
                job = live_job_queue.get(timeout=30)
                
                # Format tags for consistency
                if 'status' not in job:  # Only format if it's a job, not a control message
                    job['tags'] = {
                        'location': job.get('tag_location'),
                        'jobtype': job.get('tag_jobtype'),
                        'category': job.get('tag_category')
                    }
                
                yield f"data: {json.dumps(job)}\n\n"
                
                # If this was the completion message, we're done
                if job.get('status') == 'complete':
                    break
            except queue.Empty:
                # Send a ping event every 30 seconds to keep the connection alive
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

@main_bp.route('/send-friend-request', methods=['POST'])
def send_friend_request():
    if 'name' not in session:
        return redirect(url_for('main.home'))
    
    email = request.form.get('email')
    if email:
        current_user = User.query.filter_by(name=session['name']).first()
        
        # Rate limiting
        if not rate_limit_check(current_user.id, 'friend_request', max_requests=10, window_seconds=3600):
            flash('You have sent too many friend requests. Please try again later.', 'error')
            return redirect(url_for('main.comms'))
            
        friend = User.query.filter_by(email=email).first()
        
        if not friend:
            flash('User not found', 'error')
            return redirect(url_for('main.comms'))
            
        if friend.id == current_user.id:
            flash('You cannot send a friend request to yourself', 'error')
            return redirect(url_for('main.comms'))
            
        # Check if already friends
        if friend in current_user.friends:
            flash('You are already friends with this user', 'error')
            return redirect(url_for('main.comms'))
            
        # Check if request already exists
        existing_request = FriendRequest.query.filter_by(
            sender_id=current_user.id, receiver_id=friend.id, status='pending'
        ).first()
        
        if existing_request:
            flash('Friend request already sent', 'error')
            return redirect(url_for('main.comms'))
            
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
            return redirect(url_for('main.comms'))
        
        # Create a new request
        new_request = FriendRequest(
            sender_id=current_user.id,
            receiver_id=friend.id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        create_notification(
            friend.id, 
            f"{current_user.name} sent you a friend request", 
            link=url_for('main.comms'), 
            notification_type="friend_request"
        )
        
        flash('Friend request sent', 'success')
    else:
        flash('Please enter an email', 'error')
        
    return redirect(url_for('main.comms'))

@main_bp.route('/handle-friend-request/<int:request_id>', methods=['POST'])
def handle_friend_request(request_id):
    if 'name' not in session:
        return redirect(url_for('main.home'))
        
    current_user = User.query.filter_by(name=session['name']).first()
    friend_request = FriendRequest.query.get(request_id)
    
    # Security checks
    if not friend_request or friend_request.receiver_id != current_user.id:
        flash('Invalid request', 'error')
        return redirect(url_for('main.comms'))
        
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
    
    return redirect(url_for('main.comms'))

@main_bp.route("/add-application", methods=["POST"])
def add_application():
    if 'name' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        if request.is_json:
            # Handle JSON request from job search page
            data = request.get_json()
            
            # Parse the closing date if it exists
            closing_date = None
            if data.get('closing_date'):
                try:
                    closing_date = datetime.strptime(data['closing_date'], "%d %b %Y")
                except ValueError:
                    pass
            application = JobApplication(
                title=data['title'],
                company=data['company'],
                location=data.get('location'),
                job_type=data.get('job_type'),
                closing_date=closing_date,
                status="Saved",
                user=user,
                scraped_job_id=data.get('scraped_job_id')
            )
        else:
            # Handle form submission from job tracker page
            application = JobApplication(
                title=request.form['title'],
                company=request.form['company'],
                location=request.form.get('location'),
                job_type=request.form.get('job_type'),
                closing_date=datetime.strptime(request.form['closing_date'], "%Y-%m-%d") if request.form.get('closing_date') else None,
                status=request.form.get('status', 'Saved'),
                user=user
            )
        db.session.add(application)
        db.session.commit()
        if request.is_json:
            return jsonify({"success": True})
        return redirect(url_for("main.job_tracker"))
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        flash('Error adding application: ' + str(e), 'error')
        return redirect(url_for("main.job_tracker"))

@main_bp.route('/api/job-applications', methods=['GET'])
def get_applications():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    applications = JobApplication.query.filter_by(user=current_user).all()
    return jsonify([{
        'id': app.id,
        'title': app.title,
        'company': app.company,
        'location': app.location,
        'job_type': app.job_type,
        'closing_date': app.closing_date.strftime('%Y-%m-%d') if app.closing_date else None,
        'status': app.status,
        'date_applied': app.date_applied.strftime('%Y-%m-%d'),
        'user_id': app.user_id,
        'scraped_job_id': app.scraped_job_id
    } for app in applications])

@main_bp.route('/share-application/<int:app_id>', methods=['POST'])
def share_application(app_id):
    if 'name' not in session:
        return redirect(url_for('main.home'))
    user = User.query.filter_by(name=session['name']).first()
    application = JobApplication.query.get(app_id)
    if not application or application.user_id != user.id:
        flash('Application not found or you do not own this application', 'error')
        return redirect(url_for('main.job_tracker'))
    friend_id = request.form.get('friend_id')
    friend = User.query.get(friend_id)
    if friend and friend in user.friends:
        if application not in friend.shared_applications:
            friend.shared_applications.append(application)
            db.session.commit()
            create_notification(
                friend.id,
                f"{user.name} shared a job application at {application.company} with you",
                link=url_for('main.job_tracker'),
                notification_type="application_shared"
            )
            flash(f'Application shared with {friend.name}', 'success')
        else:
            flash('Application already shared with this friend', 'error')
    else:
        flash('Friend not found', 'error')
    return redirect(url_for('main.job_tracker'))

@main_bp.route("/update-job-status", methods=["POST"])
def update_job_status():
    job_id = request.json.get("job_id")
    new_status = request.json.get("new_status")
    job = JobApplication.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    job.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated"})

@main_bp.route('/job-tracker')
@login_required  # Require login for job tracker
def job_tracker():
    user = current_user
    # Only applications owned by the current user
    applications = JobApplication.query.filter_by(user=user).all()
    statuses = ["Saved", "Applied", "Screen", "Interviewing", "Offer", "Accepted", "Archived", "Discontinued"]
    grouped = {status: [] for status in statuses}
    for app in applications:
        grouped[app.status].append(app)
    return render_template(
        "jobtracker.html",
        active_page="job-tracker",
        grouped=grouped,
        user=user
    )

@main_bp.route('/api/notifications', methods=['GET', 'POST'])
def notifications():
    if 'name' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.filter_by(name=session['name']).first()
    
    if request.method == 'GET':
        # Get unread count for the navbar indicator
        if request.args.get('count_only') == 'true':
            unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
            return jsonify({'unread_count': unread_count})
        
        # Get notifications with pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        notifications = Notification.query\
            .filter_by(user_id=user.id)\
            .order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=per_page)
        
        result = {
            'notifications': [{
                'id': n.id,
                'content': n.content,
                'link': n.link,
                'type': n.type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat() + 'Z'  # Return ISO format with UTC timezone
            } for n in notifications.items],
            'has_next': notifications.has_next,
            'total': notifications.total
        }
        
        return jsonify(result)
    
    elif request.method == 'POST':
        # Mark notifications as read
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            Notification.query\
                .filter(Notification.id.in_(notification_ids))\
                .filter_by(user_id=user.id)\
                .update({Notification.is_read: True}, synchronize_session=False)
        else:
            # Mark all as read if no IDs specified
            Notification.query\
                .filter_by(user_id=user.id, is_read=False)\
                .update({Notification.is_read: True}, synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True})

@main_bp.route("/delete-application/<int:job_id>", methods=["DELETE"])
def delete_application(job_id):
    if 'name' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    application = JobApplication.query.get(job_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
        
    if application.user_id != user.id:
        return jsonify({"error": "Not authorized"}), 403
    try:
        db.session.delete(application)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/save-shared-application/<int:app_id>', methods=['POST'])
def save_shared_application(app_id):
    if 'name' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get the original application
    shared_app = JobApplication.query.get(app_id)
    if not shared_app:
        return jsonify({"error": "Application not found"}), 404
        
    # Check if the application is shared with the user
    if user not in shared_app.shared_with:
        return jsonify({"error": "Application not shared with you"}), 403
    
    try:
        # Create a new application for the current user
        new_app = JobApplication(
            title=shared_app.title,
            company=shared_app.company,
            location=shared_app.location,
            job_type=shared_app.job_type,
            closing_date=shared_app.closing_date,
            status="Saved",  # Always start as Saved
            user=user,
            scraped_job_id=shared_app.scraped_job_id
        )
        
        db.session.add(new_app)
        
        # Update the status in application_shares using text() and parameter binding
        db.session.execute(
            text("UPDATE application_shares SET status = 'archived' WHERE user_id = :user_id AND job_application_id = :app_id"),
            {"user_id": user.id, "app_id": app_id}
        )
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Application saved to your tracker"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@main_bp.route("/update-application/<int:job_id>", methods=["POST"])
def update_application(job_id):
    if 'name' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    user = User.query.filter_by(name=session["name"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    application = JobApplication.query.get(job_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
        
    if application.user_id != user.id:
        return jsonify({"error": "Not authorized"}), 403
        
    try:
        # Update fields
        application.title = request.form.get('title')
        application.company = request.form.get('company')
        application.location = request.form.get('location')
        application.job_type = request.form.get('job_type')
        
        closing_date = request.form.get('closing_date')
        if closing_date:
            application.closing_date = datetime.strptime(closing_date, "%Y-%m-%d")
        else:
            application.closing_date = None
            
        new_status = request.form.get('status')
        application.status = new_status
        
        db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@main_bp.route('/update-name', methods=['POST'])
def update_name():
    if 'name' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
        
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    new_name = request.form.get('new_name')
    if not new_name:
        return jsonify({"success": False, "message": "New name is required"}), 400
        
    # Update user's name
    old_name = user.name
    user.name = new_name
    
    try:
        db.session.commit()
        # Update session
        session['name'] = new_name
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            content=f"Your name has been updated from {old_name} to {new_name}",
            type="account_update",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Name updated successfully",
            "refresh": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@main_bp.route('/update-password', methods=['POST'])
def update_password():
    if 'name' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    user = User.query.filter_by(name=session['name']).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "All fields are required"}), 400
    # Check the current password hash
    if not check_password_hash(user.password, current_password):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    # Hash the new password before storing
    user.password = generate_password_hash(new_password)
    try:
        db.session.commit()
        notification = Notification(
            user_id=user.id,
            content="Your password has been updated successfully",
            type="account_update",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": "Password updated successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
