import PyPDF2
import docx2txt
import re
import json
from collections import Counter
import openai
from app.utils.fuzzy_search import job_matches
from app.models import ScrapedJob
import io
import os

OPENAI_MODEL = "gpt-3.5-turbo"

# You may want to move the API key to a config file or environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(file_stream):
    """Extract text from a PDF file."""
    try:
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
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
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
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

def extract_keywords_openai(text, direction=None, model=None, api_key=None):
    model = model or OPENAI_MODEL
    api_key = api_key or OPENAI_API_KEY
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful career advisor AI. "
                "When given a resume, you suggest job titles that fit the candidate's university studies. "
                "Only output job titles as instructed."
            )
        },
        {
            "role": "user",
            "content": (
                "Based on the following resume text, suggest exactly 6 real-world job titles that would be a good fit for this candidate. The last one should one word and very general such as 'engineering', 'software' or 'consulting'. "
                "Each job title should be a real job title (max 3 words each), and ONLY contain letters and spaces, no numbers or special characters. "
                "Output only a comma-separated list of job titles, with no explanation or extra text.\n\n"
                f"{text}"
            )
        }
    ]
    print("[DEBUG] Sending to OpenAI chat:", json.dumps(messages, indent=2))
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=50 
    )
    print("[DEBUG] Received from OpenAI chat:", response.choices[0].message.content.strip())
    keywords_str = response.choices[0].message.content.strip()
    # Try to split by comma first
    keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
    # If only one keyword and it looks like a numbered list, split by regex
    if len(keywords) == 1 and re.search(r"\d+\. ", keywords[0]):
        keywords = re.split(r"\d+\. ?", keywords[0])
        keywords = [kw.strip() for kw in keywords if kw.strip()]
    return keywords
