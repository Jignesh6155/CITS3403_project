# CareerLink

A Graduate Job Application Tracker for students: scrape jobs, analyze resumes, and manage your job search with analytics and sharing.

---

## About / Purpose

**CareerLink** is a web application designed to streamline the graduate job search process for university students. It enables users to:

- **Scrape job listings** from GradConnection in real time.
- **Upload and analyze resumes** using OpenAI's API to extract relevant keywords and receive personalized job recommendations.
- **Track job applications** with a visual dashboard, status management, and analytics.
- **Share progress and applications** with friends, fostering collaboration and accountability.

The platform is built for the UWA CITS3403 Software Project unit 2025 Semester 1.

---

## Group Members

| UWA ID   | Name                  | GitHub Username  |
|----------|-----------------------|------------------|
| 23336556 | Adriaan van der Berg  | adriaan-vdb      |
| [TODO]   | Jignesh               | [github_username]|
| [TODO]   | Rishi                 | [github_username]|

---

## Features

- **Job Scraping from GradConnection**  
  Real-time scraping of graduate and internship job listings, with filtering by location, type, and discipline.

- **Resume Keyword Extraction (OpenAI)**  
  Upload your resume (PDF/DOCX) to extract key job titles and receive AI-powered job suggestions.

- **Application Tracking Dashboard**  
  Organize applications by status (Saved, Applied, Interviewing, Offer, etc.), update progress, and archive roles.

- **Analytics & Visualizations**  
  View stats on applications sent, interviews, offers, response times, and weekly trends.

- **Friends & Sharing**  
  Add friends, send/accept friend requests, share job applications, and see shared progress.

- **Notifications**  
  In-app notifications for friend requests, shared applications, and account updates.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.x, Flask, Flask-SQLAlchemy, SQLite
- **Scraping:** Selenium
- **AI Integration:** OpenAI API (resume analysis)
- **Frontend:** HTML, CSS, JavaScript (custom, no heavy frameworks)
- **Other:** Jinja2, python-dotenv, pypdf, docx2txt

---

## Installation & Launch Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CITS3403_project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**  
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

5. **Initialize the database**  
   The database is auto-initialized on first run. For a fresh start, delete `careerlink.db` in the root.

6. **Run the Flask app**
   ```bash
   python run.py
   ```
   The app will be available at [http://localhost:5001](http://localhost:5001)

---

## Testing Instructions

Run all automated tests using `unittest`:
```bash
python3 -m unittest discover tests
```
Tests cover routes, models, utilities, and system integration.

---

## API Overview

### Public & Authenticated Endpoints

| Endpoint                       | Method(s) | Description                                      | Auth Required |
|--------------------------------|-----------|--------------------------------------------------|---------------|
| `/`                            | GET       | Home page                                        | No            |
| `/signup`, `/signin`, `/logout`| GET/POST  | User authentication                              | No            |
| `/dashboard`                   | GET       | User dashboard                                   | Yes           |
| `/job-search`                  | GET       | Job search & resume upload                       | Yes           |
| `/job-tracker`                 | GET       | Application tracker board                        | Yes           |
| `/analytics`                   | GET       | Application analytics & stats                    | Yes           |
| `/comms`                       | GET       | Friends & sharing dashboard                      | Yes           |

### Key API Endpoints

| Endpoint                        | Method(s) | Description                                      |
|----------------------------------|-----------|--------------------------------------------------|
| `/api/scraped-jobs`             | GET       | List scraped jobs (with filters, pagination)      |
| `/api/start-scraping`           | POST      | Start background scraping (Selenium)              |
| `/api/scraping-stream`          | GET       | Server-sent events for live scraping updates      |
| `/api/job-applications`         | GET       | List user's job applications                      |
| `/api/notifications`            | GET/POST  | Get or update notifications                       |
| `/upload`                       | POST      | Upload resume for analysis (OpenAI)               |
| `/update-job-status`            | POST      | Update status of a job application                |
| `/delete-application/<job_id>`  | DELETE    | Delete a job application                          |
| `/update-application/<job_id>`  | POST      | Update job application details                    |
| `/send-friend-request`          | POST      | Send a friend request                             |
| `/handle-friend-request/<id>`   | POST      | Accept/reject a friend request                    |
| `/share-application/<app_id>`   | POST      | Share an application with a friend                |
| `/save-shared-application/<id>` | POST      | Save a shared application to your tracker         |

**Note:** Most API endpoints require authentication via session.

---

## Configuration

- **Environment Variables:**  
  - `OPENAI_API_KEY` (required for resume analysis)
  - `SECRET_KEY` (set in `app/config.py` or via `.env` for production)
- **Database:**  
  - Default: SQLite (`careerlink.db`)
  - For testing: in-memory SQLite

---

## Project Structure

```
CITS3403_project/
├── app/
│   ├── static/         # CSS, JS, images
│   ├── templates/      # HTML templates (Jinja2)
│   ├── utils/          # Scraper, resume analysis, helpers
│   ├── models.py       # SQLAlchemy models
│   ├── routes.py       # Flask routes & API
│   ├── config.py       # App configuration
│   └── __init__.py
├── instance/
├── tests/              # Unit and integration tests
├── requirements.txt
├── run.py
└── .env
```

---

## Notes & Recommendations

- **Chrome is required** for Selenium-based scraping.
- The `.env` file is ignored by git for security.
- For production, set a strong `SECRET_KEY` and use a production-ready database.
