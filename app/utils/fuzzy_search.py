import json
import difflib

def job_matches(job, search='', location='', job_type='', category='', confidence=0.5):
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
        overview = ' '.join(json.loads(job.overview) if job.overview else []).lower()
        responsibilities = ' '.join(json.loads(job.responsibilities) if job.responsibilities else []).lower()
        requirements = ' '.join(json.loads(job.requirements) if job.requirements else []).lower()
        skills_and_qualities = ' '.join(json.loads(job.skills_and_qualities) if job.skills_and_qualities else []).lower()
        salary_info = ' '.join(json.loads(job.salary_info) if job.salary_info else []).lower()
        about = json.loads(job.about_company) if job.about_company else []
        about_company = ' '.join(about).lower() if about else ''
        if about and len(about) > 0:
            company = about[0].lower()
    except Exception:
        pass
    full_text = (job.full_text or '').lower()
    loc_match = location in full_text if location else True
    type_match = job_type in full_text if job_type else True
    cat_match = category in full_text if category else True
    search_match = True
    if search:
        search_match = (
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
            search in title or search in company or search in ai_summary or search in overview or
            search in responsibilities or search in requirements or search in skills_and_qualities or
            search in salary_info or search in about_company or search in full_text
        )
    return loc_match and type_match and cat_match and search_match 