import PyPDF2
import docx2txt
import re
import json
from collections import Counter

# Common job-related keywords to look for
COMMON_SKILLS = [
    # Programming languages
    "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust",
    # Web technologies
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "spring",
    # Database
    "sql", "mysql", "postgresql", "mongodb", "firebase", "oracle", "nosql", "redis",
    # Cloud
    "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform", "devops",
    # Data science
    "machine learning", "data analysis", "tensorflow", "pytorch", "pandas", "numpy", "data science",
    "statistics", "r", "tableau", "power bi", "data visualization", "big data", "hadoop", "spark",
    # Soft skills
    "communication", "teamwork", "leadership", "problem solving", "critical thinking",
    "time management", "creativity", "adaptability", "project management", "agile", "scrum",
    # Design
    "ui", "ux", "user interface", "user experience", "figma", "sketch", "adobe", "photoshop",
    "illustrator", "xd", "indesign", "graphic design",
    # Business
    "marketing", "sales", "business analysis", "product management", "strategy", "operations"
]

def extract_text_from_pdf(file_stream):
    """Extract text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_stream):
    """Extract text from a DOCX file."""
    try:
        text = docx2txt.process(file_stream)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text(file_stream, content_type):
    """Extract text from a resume file based on its content type."""
    if "pdf" in content_type:
        return extract_text_from_pdf(file_stream)
    elif "docx" in content_type or "document" in content_type:
        return extract_text_from_docx(file_stream)
    return ""

def extract_keywords(text):
    """Extract keywords from resume text."""
    # Clean the text
    text = text.lower()
    
    # Extract keywords that match our skills list
    found_keywords = []
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found_keywords.append(skill)
    
    # Count frequency of each keyword
    word_counts = Counter(found_keywords)
    
    # Return the top 10 keywords
    return [kw for kw, _ in word_counts.most_common(10)]

def find_suggested_jobs(keywords, scraped_jobs, max_suggestions=5):
    """Find jobs that match the extracted keywords."""
    job_matches = []
    
    for job in scraped_jobs:
        match_score = 0
        job_text = ""
        
        # Combine all relevant job fields into a single text
        if job.title:
            job_text += job.title + " "
        if job.ai_summary:
            job_text += job.ai_summary + " "
        if job.full_text:
            job_text += job.full_text + " "
            
        # Add structured data if available
        for field in ['overview', 'responsibilities', 'requirements', 'skills_and_qualities']:
            try:
                field_data = getattr(job, field)
                if field_data:
                    field_list = json.loads(field_data)
                    job_text += " ".join(field_list) + " "
            except (json.JSONDecodeError, AttributeError):
                pass
        
        job_text = job_text.lower()
        
        # Calculate match score based on keyword presence
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', job_text):
                match_score += 1
        
        if match_score > 0:
            job_matches.append({
                'id': job.id,
                'title': job.title,
                'company': getattr(job, 'company', ''),
                'score': match_score,
                'link': job.link
            })
    
    # Sort by match score (descending)
    job_matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top matches
    return job_matches[:max_suggestions] 