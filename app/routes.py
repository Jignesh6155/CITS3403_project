from flask import render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from app import app
from app.models import db, User, JobApplication
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
    
    # Get application counts for user and friends
    leaderboard_data = []
    
    # Add current user's data
    user_apps_count = JobApplication.query.filter_by(owner_id=user.id).count()
    leaderboard_data.append({
        'name': user.name,
        'apps_count': user_apps_count,
        'is_current_user': True
    })
    
    # Add friends' data
    for friend in user.friends:
        friend_apps_count = JobApplication.query.filter_by(owner_id=friend.id).count()
        leaderboard_data.append({
            'name': friend.name,
            'apps_count': friend_apps_count,
            'is_current_user': False
        })
    
    # Sort by application count (descending)
    leaderboard_data.sort(key=lambda x: x['apps_count'], reverse=True)
    
    # Add rank to each entry
    for i, entry in enumerate(leaderboard_data):
        entry['rank'] = i + 1
    
    # Get stats for the chart
    chart_data = {
        'labels': ['Apps Sent', 'Interviews', 'Offers'],
        'datasets': []
    }
    
    # Add current user's stats
    user_stats = {
        'Apps Sent': JobApplication.query.filter_by(owner_id=user.id).count(),
        'Interviews': JobApplication.query.filter_by(owner_id=user.id, status='Interviewing').count(),
        'Offers': JobApplication.query.filter_by(owner_id=user.id, status='Offer').count()
    }
    chart_data['datasets'].append({
        'label': 'You',
        'data': [user_stats['Apps Sent'], user_stats['Interviews'], user_stats['Offers']],
        'backgroundColor': 'rgba(99, 102, 241, 0.7)'
    })
    
    # Add friends' stats (top 2 friends)
    colors = ['rgba(34, 197, 94, 0.7)', 'rgba(234, 179, 8, 0.7)']
    for i, friend in enumerate(user.friends[:2]):
        friend_stats = {
            'Apps Sent': JobApplication.query.filter_by(owner_id=friend.id).count(),
            'Interviews': JobApplication.query.filter_by(owner_id=friend.id, status='Interviewing').count(),
            'Offers': JobApplication.query.filter_by(owner_id=friend.id, status='Offer').count()
        }
        chart_data['datasets'].append({
            'label': friend.name,
            'data': [friend_stats['Apps Sent'], friend_stats['Interviews'], friend_stats['Offers']],
            'backgroundColor': colors[i % len(colors)]
        })
    
    # Get applications shared with the current user
    shared_apps = user.shared_applications  
    
    return render_template("comms.html", 
                         active_page="comms", 
                         current_user=user,
                         leaderboard_data=leaderboard_data,
                         chart_data=chart_data,
                         shared_apps=shared_apps)
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

@app.route('/add-friend', methods=['POST'])
def add_friend():
    if 'name' not in session:
        return redirect(url_for('home'))
    
    email = request.form.get('email')
    if email:
        user = User.query.filter_by(name=session['name']).first()
        
        # Check if user is trying to add themselves
        if email == user.email:
            flash('You cannot add yourself as a friend', 'error')
            return redirect(url_for('comms'))
        
        friend = User.query.filter_by(email=email).first()
        if friend:
            # Check if they're already friends
            if friend in user.friends:
                flash('You are already friends with this user', 'error')
            else:
                user.friends.append(friend)
                db.session.commit()
                flash('Friend added successfully', 'success')
        else:
            flash('User not found', 'error')
    else:
        flash('Please enter an email', 'error')
    
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

@app.route("/job-tracker")
def job_tracker():
    if 'name' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(name=session['name']).first()
    applications = JobApplication.query.filter_by(owner=user).all()

    statuses = ["Saved", "Applied", "Screen", "Interviewing", "Offer", "Accepted", "Archived", "Discontinued"]
    grouped = {status: [] for status in statuses}
    for app in applications:
        grouped[app.status].append(app)

    return render_template("jobtracker.html", 
                          active_page="job-tracker", 
                          grouped=grouped,
                          current_user=user)  

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

@app.route('/save-shared-application/<int:app_id>', methods=['POST'])
def save_shared_application(app_id):
    if 'name' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.filter_by(name=session['name']).first()
    shared_app = JobApplication.query.get(app_id)
    
    if not shared_app or shared_app not in user.shared_applications:
        return jsonify({'error': 'Application not found or not shared with you'}), 404
    
    # Create a copy of the shared application for the current user
    new_app = JobApplication(
        company=shared_app.company,
        title=shared_app.title,
        status='Saved',  # Default status when saving
        date_applied=None,  # User hasn't applied yet
        owner_id=user.id
    )
    
    db.session.add(new_app)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Application saved to your tracker'})


