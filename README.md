# CareerLink

A web application for job tracking, resume analysis, and job recommendations for university students.

## Features
- User authentication (sign up, sign in)
- Resume upload and analysis (PDF/DOCX)
- Job recommendations using OpenAI
- Job scraping from GradConnection
- Job tracker board

## Setup Instructions

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd CITS3403_project
```

### 2. Create and activate a virtual environment (optional but recommended)
```sh
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```sh
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Run the application
```sh
python run.py
```
The app will be available at [http://localhost:5001](http://localhost:5001)

## Project Structure
```
CITS3403_project/
├── app/
│   ├── static/
│   ├── templates/
│   ├── utils/
│   ├── models.py
│   ├── routes.py
│   └── __init__.py
├── instance/
├── requirements.txt
├── run.py
└── .env
```

## Notes
- Make sure you have Chrome installed for Selenium-based scraping.
- The `.env` file is ignored by git for security.
- For any issues, please open an issue or contact the maintainer.
