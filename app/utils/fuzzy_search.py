import json
import difflib

"""
Utilities for fuzzy searching and matching job listings.

This module provides functions to perform fuzzy string matching and to determine if a job listing matches
user-specified search criteria, even when the input is not an exact match. This is useful for improving
search experience by allowing for typos, partial matches, and flexible filtering.
"""


def is_fuzzy_match(needle, haystack, threshold=0.6):
    """
    Determines if the 'needle' string is a fuzzy match within the 'haystack' string.

    Args:
        needle (str): The string to search for.
        haystack (str): The string to search within.
        threshold (float): Similarity ratio threshold (0 to 1) for fuzzy matching.

    Returns:
        bool: True if the needle is found in the haystack or the similarity ratio exceeds the threshold.

    This function uses both substring search and difflib's SequenceMatcher to allow for flexible, typo-tolerant matching.
    """
    return (
        needle in haystack or
        difflib.SequenceMatcher(None, needle, haystack).ratio() > threshold
    )


def job_matches(job, search='', location='', job_type='', category='', confidence=0.6):
    """
    Determines if a job listing matches the provided search criteria using fuzzy matching.

    Args:
        job: An object representing a job listing, expected to have various string fields.
        search (str): Free-text search query to match against job fields.
        location (str): Location filter to match against job content.
        job_type (str): Job type filter (e.g., 'Full-time', 'Part-time').
        category (str): Category filter (e.g., 'Engineering', 'Marketing').
        confidence (float): Similarity threshold for fuzzy matching (0 to 1).

    Returns:
        bool: True if the job matches all provided criteria, False otherwise.

    This function aggregates multiple fields from the job object, applies fuzzy matching to each,
    and returns True only if all filters (location, job_type, category, and search) are satisfied.
    """
    # Normalize and extract relevant job fields for matching
    title = (job.title or '').lower()
    company = ''
    ai_summary = (job.ai_summary or '').lower()
    overview = ''
    responsibilities = ''
    requirements = ''
    skills_and_qualities = ''
    salary_info = ''
    about_company = ''
    
    try:
        # Many fields are stored as JSON arrays; join them into single strings for searching
        overview = ' '.join(json.loads(job.overview) if job.overview else []).lower()
        responsibilities = ' '.join(json.loads(job.responsibilities) if job.responsibilities else []).lower()
        requirements = ' '.join(json.loads(job.requirements) if job.requirements else []).lower()
        skills_and_qualities = ' '.join(json.loads(job.skills_and_qualities) if job.skills_and_qualities else []).lower()
        salary_info = ' '.join(json.loads(job.salary_info) if job.salary_info else []).lower()
        about = json.loads(job.about_company) if job.about_company else []
        about_company = ' '.join(about).lower() if about else ''
        # Heuristic: use the first element of 'about_company' as the company name if available
        if about and len(about) > 0:
            company = about[0].lower()
    except Exception:
        # If any field fails to parse, leave it as an empty string
        pass

    # Fallback: use the full_text field for broad matching
    full_text = (job.full_text or '').lower()

    # Fuzzy match for dropdown filters; if filter is empty, treat as a match (no filter applied)
    loc_match = is_fuzzy_match(location, full_text, threshold=confidence) if location else True
    type_match = is_fuzzy_match(job_type, full_text, threshold=confidence) if job_type else True
    cat_match = is_fuzzy_match(category, full_text, threshold=confidence) if category else True

    # Fuzzy match for the main search query across all relevant fields
    search_match = True
    if search:
        search = search.lower()
        search_match = (
            # Fuzzy match against each field
            difflib.SequenceMatcher(None, search, title).ratio() > confidence or
            difflib.SequenceMatcher(None, search, company).ratio() > confidence or
            difflib.SequenceMatcher(None, search, ai_summary).ratio() > confidence or
            difflib.SequenceMatcher(None, search, overview).ratio() > confidence or
            difflib.SequenceMatcher(None, search, responsibilities).ratio() > confidence or
            difflib.SequenceMatcher(None, search, requirements).ratio() > confidence or
            difflib.SequenceMatcher(None, search, skills_and_qualities).ratio() > confidence or
            difflib.SequenceMatcher(None, search, salary_info).ratio() > confidence or
            difflib.SequenceMatcher(None, search, about_company).ratio() > confidence or
            difflib.SequenceMatcher(None, search, full_text).ratio() > confidence or
            # Also allow for direct substring matches for efficiency
            search in title or search in company or search in ai_summary or search in overview or
            search in responsibilities or search in requirements or search in skills_and_qualities or
            search in salary_info or search in about_company or search in full_text
        )

    # Only return True if all filters are satisfied
    return loc_match and type_match and cat_match and search_match
