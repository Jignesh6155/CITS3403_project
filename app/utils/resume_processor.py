import pypdf
import docx2txt
import re
import json
from collections import Counter
import openai
from app.utils.fuzzy_search import job_matches
from app.models import ScrapedJob
import io
import os

"""
Resume processing utilities for extracting and analyzing resume content.

This module provides functions to extract text from PDF and DOCX resumes, interface with OpenAI for
keyword/job title extraction, and support downstream matching of resumes to job listings. It is designed
to be robust to different file types and to facilitate AI-driven resume analysis for job recommendation systems.
"""

OPENAI_MODEL = "gpt-3.5-turbo"

# The OpenAI API key should be set as an environment variable for security and flexibility.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(file_stream, debug=False):
    """
    Extracts text content from a PDF file stream.

    Args:
        file_stream (bytes or file-like): The PDF file data or stream.
        debug (bool): If True, prints error messages for debugging.

    Returns:
        str: The extracted text from the PDF, or an empty string on failure.

    This function uses the pypdf library to read and extract text from each page of the PDF.
    It handles both bytes and file-like objects for flexibility in file uploads.
    """
    try:
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
        reader = pypdf.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        if debug:
            print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_stream, debug=False):
    """
    Extracts text content from a DOCX file stream.

    Args:
        file_stream (bytes or file-like): The DOCX file data or stream.
        debug (bool): If True, prints error messages for debugging.

    Returns:
        str: The extracted text from the DOCX, or an empty string on failure.

    This function uses the docx2txt library to extract all text from the DOCX file.
    It handles both bytes and file-like objects for flexibility in file uploads.
    """
    try:
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
        text = docx2txt.process(file_stream)
        return text
    except Exception as e:
        if debug:
            print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text(file_stream, content_type, debug=False):
    """
    Extracts text from a resume file based on its MIME content type.

    Args:
        file_stream (bytes or file-like): The resume file data or stream.
        content_type (str): The MIME type of the file (e.g., 'application/pdf').
        debug (bool): If True, prints error messages for debugging.

    Returns:
        str: The extracted text from the file, or an empty string if unsupported type or failure.

    This function delegates to the appropriate extraction function based on file type.
    """
    if "pdf" in content_type:
        return extract_text_from_pdf(file_stream, debug=debug)
    elif "docx" in content_type or "document" in content_type:
        return extract_text_from_docx(file_stream, debug=debug)
    return ""

def extract_keywords_openai(text, direction=None, model=None, api_key=None):
    """
    Uses OpenAI's language model to extract relevant job titles from resume text.

    Args:
        text (str): The resume text to analyze.
        direction (str, optional): Reserved for future prompt customization.
        model (str, optional): The OpenAI model to use (defaults to OPENAI_MODEL).
        api_key (str, optional): The OpenAI API key (defaults to environment variable).

    Returns:
        list[str]: A list of job titles suggested by the AI, or an empty list on failure.

    This function sends a carefully crafted prompt to the OpenAI API, requesting a comma-separated list
    of real-world job titles that fit the candidate's background. It parses the response and returns the list.
    """
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
    # The OpenAI API is called with a strict prompt to ensure a clean, parseable response.
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=50 
    )
    keywords_str = response.choices[0].message.content.strip()
    # Try to split by comma first for standard output
    keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
    # If only one keyword and it looks like a numbered list, split by regex as a fallback
    if len(keywords) == 1 and re.search(r"\d+\. ", keywords[0]):
        keywords = re.split(r"\d+\. ?", keywords[0])
        keywords = [kw.strip() for kw in keywords if kw.strip()]
    return keywords
