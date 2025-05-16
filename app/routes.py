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
from app.extensions import csrf


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
SCRAPE_SIZE = 1
# ─────────────────────────────────────────────────────────────────────────────
def background_scraper(
    app,
    user_id: int = 1,
    jobtype: str = "internships",
    discipline: str | None = None,
    location: str | None = None,
    keyword: str | None = None,
) -> None:
    """
    Run GradConnection scraping in a detached thread and stream results into
    `live_job_queue`.  All DB and Flask-config access happens *inside* an
    app-context so `current_app`, `db`, etc. are safe to use.
    """
    # IMPORTANT: do **not** touch current_app before we open the context
    # -----------------------------------------------------------------
    with app.app_context():

        debug = app.config.get("DEBUG", False)
        if debug:
            print(f"[SCRAPER] starting: user={user_id} jobtype={jobtype} "
                  f"discipline={discipline} location={location} keyword={keyword}")

        from app.utils.scraper_GC_jobs_detailed import get_jobs_full
        from app.models import ScrapedJob   # local import – ctx is active

        try:
            jobs = get_jobs_full(
                jobtype=jobtype,
                discipline=discipline,
                location=location,
                keyword=keyword,
                max_pages=SCRAPE_SIZE,
                headless=HEADLESS_TOGGLE,
            )
            if debug:
                print(f"[SCRAPER] {len(jobs)} jobs scraped")

            # clear previous search results for this (user, filter) combo
            ScrapedJob.query.filter_by(
                user_id=user_id,
                tag_jobtype=jobtype,
                tag_location=location,
                tag_category=discipline,
            ).delete()
            db.session.commit()

            perth_tz = pytz.timezone("Australia/Perth")

            for idx, job in enumerate(jobs, 1):
                # ---------- closing-date massaging ---------------------
                closing_in  = job.get("closing_in", "") or ""
                closing_date = None
                if closing_in:
                    now = datetime.now(perth_tz)
                    txt = closing_in.lower()
                    d_m = re.search(r"(\d+)\s*days?",  txt)
                    m_m = re.search(r"(\d+)\s*months?", txt)
                    h_m = re.search(r"(\d+)\s*hours?",  txt)

                    if "an hour" in txt or h_m:
                        closing_date = now            # today
                        hours = int(h_m.group(1)) if h_m else 1
                        closing_in  = f"Closing in {hours} hour{'s' if hours>1 else ''}"
                    elif "a day" in txt or d_m:
                        days = 1 if "a day" in txt else int(d_m.group(1))
                        closing_date = now + timedelta(days=days)
                        closing_in  = f"Closing in {days} day{'s' if days>1 else ''}"
                    elif "a month" in txt or m_m:
                        months = 1 if "a month" in txt else int(m_m.group(1))
                        closing_date = now + timedelta(days=30*months)
                        closing_in  = f"Closing in {months} month{'s' if months>1 else ''}"
                    # else: leave closing_date = None

                # ---------- DB insert ---------------------------------
                scraped = ScrapedJob(
                    user_id        = user_id,
                    title          = job.get("title"),
                    posted_date    = job.get("posted_date"),
                    closing_in     = closing_in,
                    closing_date   = closing_date,
                    ai_summary     = job.get("ai_summary"),
                    overview       = json.dumps(job.get("overview", [])),
                    responsibilities= json.dumps(job.get("responsibilities", [])),
                    requirements   = json.dumps(job.get("requirements", [])),
                    skills_and_qualities = json.dumps(job.get("skills_and_qualities", [])),
                    salary_info    = json.dumps(job.get("salary_info", [])),
                    about_company  = json.dumps(job.get("about_company", [])),
                    full_text      = job.get("full_text"),
                    link           = job.get("link"),
                    source         = "GradConnection",
                    tag_location   = location,
                    tag_jobtype    = jobtype,
                    tag_category   = discipline,
                )
                db.session.add(scraped)
                db.session.commit()

                # ---------- push to SSE queue -------------------------
                about = job.get("about_company", [])
                live_job_queue.put({
                    "title"       : scraped.title,
                    "company"     : about[0] if about else "",
                    "posted_date" : scraped.posted_date,
                    "closing_in"  : scraped.closing_in,
                    "closing_date": closing_date.strftime("%d %b %Y") if closing_date else None,
                    "ai_summary"  : scraped.ai_summary,
                    "link"        : scraped.link,
                    "tag_location": location,
                    "tag_jobtype" : jobtype,
                    "tag_category": discipline,
                })

                if debug:
                    print(f"[SCRAPER] ({idx}/{len(jobs)}) queued: {scraped.title}")

                time.sleep(0.1)   # polite pause for the stream

        except Exception as exc:
            db.session.rollback()
            print("[SCRAPER] ERROR:", exc)
            import traceback; traceback.print_exc()

        finally:
            live_job_queue.put({"status": "complete"})
            if debug:
                print("[SCRAPER] finished – sentinel queued")
# ─────────────────────────────────────────────────────────────────────────────


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
        session['email'] = new_user.email
        session['name'] = new_user.name
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
            session['email'] = user.email
            session['name'] = user.name
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

@main_bp.route("/comms")
@login_required
def comms():
    # Get all friends
    friends = current_user.friends.all()
    
    # Get friend requests for recent sorting
    friend_requests = {}
    for friend in friends:
        request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == friend.id)) |
            ((FriendRequest.sender_id == friend.id) & (FriendRequest.receiver_id == current_user.id))
        ).order_by(FriendRequest.updated_at.desc()).first()
        if request:
            friend_requests[friend.id] = request
    
    # Get shared apps count and status for sorting
    shared_apps_count = {}
    shared_apps = []
    app_statuses = {}
    
    # Get applications shared with current user
    shared_with_user = db.session.query(JobApplication, application_shares.c.status).join(
        application_shares,
        JobApplication.id == application_shares.c.job_application_id
    ).filter(
        application_shares.c.user_id == current_user.id
    ).all()
    
    for app, status in shared_with_user:
        shared_apps.append(app)
        app_statuses[app.id] = status
    
    # Get applications shared by current user
    shared_by_user = db.session.query(JobApplication, application_shares.c.status).join(
        application_shares,
        JobApplication.id == application_shares.c.job_application_id
    ).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    for app, status in shared_by_user:
        if app not in shared_apps:
            shared_apps.append(app)
            app_statuses[app.id] = status
    
    # Count shared apps per friend
    for friend in friends:
        count = db.session.query(application_shares).filter(
            ((application_shares.c.user_id == current_user.id) & (application_shares.c.job_application_id.in_(
                db.session.query(JobApplication.id).filter_by(user_id=friend.id)
            ))) |
            ((application_shares.c.user_id == friend.id) & (application_shares.c.job_application_id.in_(
                db.session.query(JobApplication.id).filter_by(user_id=current_user.id)
            )))
        ).count()
        shared_apps_count[friend.id] = count
    
    return render_template(
        'comms.html',
        active_page="comms",
        user=current_user,
        friends=friends,
        friend_requests=friend_requests,
        shared_apps_count=shared_apps_count,
        shared_apps=shared_apps,
        app_statuses=app_statuses
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


# ------------------------------------------------------------------ #
#  SCRAPED-JOBS JSON  ➜  /api/scraped-jobs
# ------------------------------------------------------------------ #
@main_bp.route("/api/scraped-jobs")
def api_scraped_jobs():
    print("\n=== [/api/scraped-jobs] request received =====================")
    try:
        # ── query-string params ────────────────────────────────────────
        search    = request.args.get("search",    "").strip().lower()
        location  = request.args.get("location",  "").strip().lower()
        job_type  = request.args.get("type",      "").strip().lower()
        category  = request.args.get("category",  "").strip().lower()
        offset    = int(request.args.get("offset", 0))
        limit     = int(request.args.get("limit", 10))

        print(f"[ARGS] search='{search}' location='{location}' "
              f"type='{job_type}' category='{category}' offset={offset} limit={limit}")

        # ── DB query & Python filtering  ───────────────────────────────
        jobs = ScrapedJob.query.all()
        print(f"[DB] fetched {len(jobs)} rows from scraped_job")

        filtered  = [j for j in jobs if job_matches(j, search, location,
                                                    job_type, category)]
        total     = len(filtered)
        paginated = filtered[offset: offset + limit]

        print(f"[FILTER] {total} match filters, returning {len(paginated)} rows")

        # ── serialise results  ─────────────────────────────────────────
        result = []
        for idx, job in enumerate(paginated, 1):
            try:
                about = json.loads(job.about_company) if job.about_company else []
            except Exception as ex:
                print(f"[WARN] json.loads failed for job.id={job.id}: {ex}")
                about = []

            closing_date_str = (
                job.closing_date.strftime("%d %b %Y")
                if job.closing_date else None
            )

            result.append({
                "title":        job.title,
                "company":      about[0] if about else "",
                "posted_date":  job.posted_date,
                "closing_in":   job.closing_in,
                "closing_date": closing_date_str,
                "ai_summary":   job.ai_summary,
                "link":         job.link,
                "tags": {
                    "location": job.tag_location or None,
                    "jobtype":  job.tag_jobtype or None,
                    "category": job.tag_category or None,
                },
            })
            print(f"[SERIALISE] #{idx}  job.id={job.id} title='{job.title}'")

        payload = {"jobs": result,
                   "has_more": offset + limit < total,
                   "total": total}
        print("[RETURN] sending JSON payload")
        print("============================================================\n")
        return jsonify(payload)

    except Exception as e:
        print("[ERROR] in /api/scraped-jobs:", e)
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# ------------------------------------------------------------------ #
#  START BACKGROUND SCRAPE  ➜  /api/start-scraping   (POST)
# ------------------------------------------------------------------ #
@main_bp.route("/api/start-scraping", methods=["POST"])
@csrf.exempt
def api_start_scraping():
    print("\n=== [/api/start-scraping] POST received =====================")
    try:
        user = current_user          # may be Anonymous if no login
        print(f"[AUTH] current_user id={getattr(user,'id',None)} "
              f"auth={user.is_authenticated if user else False}")

        data = request.get_json(force=True) or {}
        print(f"[JSON] {data}")

        jobtype    = data.get("jobtype",    "internships")
        discipline = data.get("discipline") or None
        location   = data.get("location")   or None
        keyword    = data.get("keyword")    or None
        print(f"[PARAMS] jobtype={jobtype} discipline={discipline} "
              f"location={location} keyword={keyword}")

        if user.is_authenticated and not rate_limit_check(user.id, "scraping"):
            print("[RATE] hit limit – rejecting")
            return jsonify({"error": "Rate limit exceeded"}), 429

        print("[THREAD] kicking off background_scraper() …")
        app = current_app._get_current_object()
        threading.Thread(
            target=background_scraper,
            args=(app, getattr(user, "id", 1), jobtype, discipline, location, keyword),
            daemon=True
        ).start()
        print("[THREAD] started OK")
        print("============================================================\n")
        return "", 202

    except Exception as e:
        print("[ERROR] in /api/start-scraping:", e)
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# ------------------------------------------------------------------ #
#  SERVER-SENT EVENTS STREAM  ➜  /api/scraping-stream
# ------------------------------------------------------------------ #
@main_bp.route("/api/scraping-stream")
def api_scraping_stream():
    print("\n=== [/api/scraping-stream] client connected ================")

    def event_stream():
        print("[SSE] generator entered")
        while True:
            try:
                job = live_job_queue.get(timeout=30)
                print(f"[SSE] dequeued → {job}")

                if 'status' not in job:          # normal job payload
                    job["tags"] = {
                        "location": job.get("tag_location"),
                        "jobtype":  job.get("tag_jobtype"),
                        "category": job.get("tag_category"),
                    }

                yield f"data: {json.dumps(job)}\n\n"

                if job.get("status") == "complete":
                    print("[SSE] scrape complete – closing stream")
                    break

            except queue.Empty:
                print("[SSE] queue empty – sending keep-alive ping")
                yield 'data: {"type":"ping"}\n\n'

            except GeneratorExit:
                # client disconnected
                print("[SSE] client disconnected")
                break

            except Exception as ex:
                print("[SSE] unexpected error:", ex)
                import traceback; traceback.print_exc()
                break

        print("[SSE] generator exiting")

    response = Response(stream_with_context(event_stream()),
                        mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    print("============================================================\n")
    return response



@main_bp.route('/send-friend-request', methods=['POST'])
@login_required
def send_friend_request():
    email = request.form.get('email')
    user = current_user
    if email:
        # Rate limiting
        if not rate_limit_check(user.id, 'friend_request', max_requests=10, window_seconds=3600):
            flash('You have sent too many friend requests. Please try again later.', 'error')
            return redirect(url_for('main.comms'))
        friend = User.query.filter_by(email=email).first()
        if not friend:
            flash('User not found', 'error')
            return redirect(url_for('main.comms'))
        if friend.id == user.id:
            flash('You cannot send a friend request to yourself', 'error')
            return redirect(url_for('main.comms'))
        # Check if already friends
        if friend in user.friends:
            flash('You are already friends with this user', 'error')
            return redirect(url_for('main.comms'))
        # Check if request already exists
        existing_request = FriendRequest.query.filter_by(
            sender_id=user.id, receiver_id=friend.id, status='pending'
        ).first()
        if existing_request:
            flash('Friend request already sent', 'error')
            return redirect(url_for('main.comms'))
        # Check if there's a request from the other user
        existing_reverse_request = FriendRequest.query.filter_by(
            sender_id=friend.id, receiver_id=user.id, status='pending'
        ).first()
        if existing_reverse_request:
            # Auto-accept the other request
            existing_reverse_request.status = 'accepted'
            # Ensure bidirectional friendship
            user.friends.append(friend)
            friend.friends.append(user)
            db.session.commit()
            flash(f'You are now friends with {friend.name}', 'success')
            return redirect(url_for('main.comms'))
        # Create a new request
        new_request = FriendRequest(
            sender_id=user.id,
            receiver_id=friend.id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        create_notification(
            friend.id, 
            f"{user.name} sent you a friend request", 
            link=url_for('main.comms'), 
            notification_type="friend_request"
        )
        flash('Friend request sent', 'success')
    else:
        flash('Please enter an email', 'error')
    return redirect(url_for('main.comms'))

@main_bp.route('/handle-friend-request/<int:request_id>', methods=['POST'])
@login_required
def handle_friend_request(request_id):
    user = current_user
    friend_request = FriendRequest.query.get(request_id)
    # Security checks
    if not friend_request or friend_request.receiver_id != user.id:
        flash('Invalid request', 'error')
        return redirect(url_for('main.comms'))
    action = request.form.get('action')
    if action == 'accept':
        friend_request.status = 'accepted'
        # Add to friends (both ways)
        sender = User.query.get(friend_request.sender_id)
        # Ensure bidirectional friendship
        user.friends.append(sender)
        sender.friends.append(user)
        db.session.commit()
        flash(f'You are now friends with {sender.name}', 'success')
    elif action == 'reject':
        friend_request.status = 'rejected'
        db.session.commit()
        flash('Friend request rejected', 'success')
    return redirect(url_for('main.comms'))

@main_bp.route("/add-application", methods=["POST"])
@login_required
def add_application():
    print("[DEBUG] /add-application route entered")
    print("[DEBUG] request.is_json:", request.is_json)
    print("[DEBUG] request.data:", request.data)
    print("[DEBUG] request.form:", request.form)
    from flask_login import current_user
    print("[DEBUG] current_user.is_authenticated:", current_user.is_authenticated)
    from flask import current_app
    debug = current_app.config.get('DEBUG', False)
    try:
        if request.is_json:
            data = request.get_json()
            if debug:
                print("[DEBUG] /add-application (JSON):", data)
                print("[DEBUG] Current user:", current_user)
            # Check for required fields
            missing = [k for k in ['title', 'company'] if not data.get(k)]
            if missing and debug:
                print(f"[DEBUG] Missing required fields: {missing}")
            # Parse the closing date if it exists
            closing_date = None
            if data.get('closing_date'):
                try:
                    closing_date = datetime.strptime(data['closing_date'], "%d %b %Y")
                except ValueError:
                    if debug:
                        print("[DEBUG] Invalid closing_date format:", data.get('closing_date'))
            application = JobApplication(
                title=data['title'],
                company=data['company'],
                location=data.get('location'),
                job_type=data.get('job_type'),
                closing_date=closing_date,
                status="Saved",
                user=current_user,
                scraped_job_id=data.get('scraped_job_id')
            )
        else:
            if debug:
                print("[DEBUG] /add-application (FORM):", request.form)
                print("[DEBUG] Current user:", current_user)
            application = JobApplication(
                title=request.form['title'],
                company=request.form['company'],
                location=request.form.get('location'),
                job_type=request.form.get('job_type'),
                closing_date=datetime.strptime(request.form['closing_date'], "%Y-%m-%d") if request.form.get('closing_date') else None,
                status=request.form.get('status', 'Saved'),
                user=current_user
            )
        db.session.add(application)
        db.session.commit()
        if debug:
            print("[DEBUG] Application saved successfully:", application)
        if request.is_json:
            return jsonify({"success": True})
        return redirect(url_for("main.job_tracker"))
    except Exception as e:
        db.session.rollback()
        if debug:
            print("[DEBUG] Error in /add-application:", str(e))
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
@login_required
def share_application(app_id):
    user = current_user
    application = JobApplication.query.get(app_id)
    if not application or application.user_id != user.id:
        return jsonify({"success": False, "message": "Application not found or you do not own this application"}), 404
        
    friend_id = request.form.get('friend_id')
    if not friend_id:
        return jsonify({"success": False, "message": "No friend selected"}), 400
        
    friend = User.query.get(friend_id)
    if friend and friend in user.friends:
        # Check if already shared
        existing_share = db.session.query(application_shares).filter_by(
            user_id=friend.id,
            job_application_id=application.id
        ).first()
        
        if not existing_share:
            # Insert new share with active status
            db.session.execute(
                application_shares.insert().values(
                    user_id=friend.id,
                    job_application_id=application.id,
                    status='active'
                )
            )
            
            db.session.commit()
            
            create_notification(
                friend.id,
                f"{user.name} shared a job application at {application.company} with you",
                link=url_for('main.comms'),
                notification_type="application_shared"
            )
            return jsonify({"success": True, "message": f'Application shared with {friend.name}'})
        else:
            # Update existing share to active if it was archived
            if existing_share.status == 'archived':
                db.session.execute(
                    text("UPDATE application_shares SET status = 'active' WHERE user_id = :user_id AND job_application_id = :app_id"),
                    {"user_id": friend.id, "app_id": application.id}
                )
                db.session.commit()
                return jsonify({"success": True, "message": f'Application re-shared with {friend.name}'})
            else:
                return jsonify({"success": False, "message": "Application already shared with this friend"}), 400
    else:
        return jsonify({"success": False, "message": "Friend not found"}), 404

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
@login_required
def notifications():
    user = current_user
    
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
@login_required  # Use Flask-Login's decorator
def delete_application(job_id):
    # Use current_user from Flask-Login
    application = JobApplication.query.get(job_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
        
    if application.user_id != current_user.id:
        return jsonify({"error": "Not authorized"}), 403
    try:
        db.session.delete(application)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@main_bp.route('/save-shared-application/<int:app_id>', methods=['POST'])
@login_required
def save_shared_application(app_id):
    user = current_user
    
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
        
        # Update the status in application_shares to 'archived'
        from sqlalchemy import text
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
        print(f"Error saving shared application: {str(e)}")  # Add this for debugging
        return jsonify({"error": str(e)}), 500

@main_bp.route("/update-application/<int:job_id>", methods=["POST"])
@login_required
def update_application(job_id):
    user = current_user
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
@login_required
def update_name():
    user = current_user
    new_name = request.form.get('new_name')
    if not new_name:
        return jsonify({"success": False, "message": "New name is required"}), 400
    old_name = user.name
    user.name = new_name
    try:
        db.session.commit()
        session['name'] = new_name
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
@login_required
def update_password():
    user = current_user
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "All fields are required"}), 400
    if not check_password_hash(user.password, current_password):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
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
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
