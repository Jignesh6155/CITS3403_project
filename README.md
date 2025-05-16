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
| 23722513   | Jignesh               | Jignesh6155 |
| 23463452   | Rishwanth Katherapalle              | Rishi3524|

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
   pip3 install -r requirements.txt
   ```

4. **Configure environment variables**  
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-api-key
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
  - `SECRET_KEY` (required for session security; set in your .env file or environment)
  - `APP_CONFIG` (controls which configuration is used: `development`, `production`, or `testing`)
- **Database:**  
  - Default: SQLite (`careerlink.db`)
  - For testing: in-memory SQLite

---

## Application Configuration Modes

The application now selects its configuration class based on the `APP_CONFIG` environment variable. This is an industry-standard approach for flexible deployment.

### Available Configurations

- **DevelopmentConfig** (`APP_CONFIG=development`)
  - Used for local development.
  - Enables debug mode (`DEBUG=True`).
  - Uses a temporary secret key unless overridden by the `SECRET_KEY` environment variable.
  - Database: `careerlink.db` (SQLite file).

- **ProductionConfig** (`APP_CONFIG=production`)
  - Used for deployment/production.
  - Disables debug mode (`DEBUG=False`).
  - Requires `SECRET_KEY` to be set in the environment (no default fallback).
  - Database: `careerlink.db` (SQLite file, or override with your own URI).

- **TestingConfig** (`APP_CONFIG=testing`)
  - Used for running tests.
  - Enables testing mode (`TESTING=True`).
  - Uses an in-memory SQLite database (`sqlite:///:memory:`).
  - Disables CSRF protection for easier testing.
  - Uses a temporary secret key unless overridden by the `SECRET_KEY` environment variable.

### How to Use a Configuration

By default, the app uses `DevelopmentConfig` unless you specify otherwise. To change the configuration, set the `APP_CONFIG` environment variable:

- **In your shell or .env file:**
  ```bash
  export APP_CONFIG=production
  # or
  export APP_CONFIG=testing
  ```
  Or in `.env`:
  ```
  APP_CONFIG=production
  ```

- **What this does:**
  - `APP_CONFIG=development` → DevelopmentConfig
  - `APP_CONFIG=production` → ProductionConfig
  - `APP_CONFIG=testing` → TestingConfig

- **No need to edit `run.py` to change environments!**

### Setting Other Environment Variables

- Create a `.env` file in your project root:
  ```
  SECRET_KEY=your-very-secret-key
  OPENAI_API_KEY=your-openai-api-key
  APP_CONFIG=development  # or production, or testing
  ```
- Or set the environment variable directly in your shell:
  ```bash
  export SECRET_KEY=your-very-secret-key
  export OPENAI_API_KEY=your-openai-api-key
  export APP_CONFIG=production
  ```

**Note:**
- For production, always set a strong `SECRET_KEY` and do not rely on defaults.
- For development and testing, defaults are provided for convenience, but you can override them with your own environment variables.

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

---

| **Requirement**              | **Implementation** |
|------------------------------|--------------------|
| **Introductory View**        | Provides a landing page with account creation and login (`/index`, `/signin`). After login, users are welcomed with a personalized dashboard view. |
| **Upload Private Data**      | Users can upload resumes (PDF/DOCX) via the `/job-search` page. Uploaded files are securely processed using OpenAI’s API for keyword extraction and job suggestions. |
| **Visualize Data**           | The `/analytics` page provides interactive data visualizations using Chart.js, showing application statistics, success rates, and trends over time. |
| **Selectively Share Data**   | Users can add friends, send/accept friend requests, and share specific job applications through the `/comms` page, allowing selective data sharing. |
| **Engaging Design**          | The UI is built with Tailwind CSS and Lucide icons, offering a modern, responsive design with visual feedback and hover interactions to keep users engaged. |
| **Effective Functionality**  | Features job scraping from GradConnection, AI-driven resume analysis, application tracking, and social sharing tools, directly addressing user needs. |
| **Intuitive Navigation**     | The app uses a dashboard-centered layout with clearly labeled navigation links, modals, tooltips, and smooth transitions for an easy-to-use experience. |
| **Private GitHub Repository**| Project code is maintained in a GitHub repository with version control, issue tracking, and team collaboration via Git. |
| **Comprehensive README**     | This README includes:<br>- Purpose and design explanation<br>- Group member table with UWA IDs and GitHub usernames<br>- Installation and testing instructions<br>- API documentation and project structure overview |

---
