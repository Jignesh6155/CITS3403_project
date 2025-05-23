from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json

"""
GradConnection Job Scraper Utilities

This module provides functions to scrape detailed job listings from the GradConnection website using Selenium.
It includes helpers for URL construction, robust extraction of job details (handling various page layouts),
pagination, and saving results to a database. Designed for use in automated job aggregation and enrichment pipelines.
"""

# ───────────────────────────── helpers ────────────────────────────────────────
def build_url(jobtype: str, discipline: str | None = None, location: str | None = None, keyword: str | None = None) -> str:
    """
    Construct a GradConnection search URL based on job type, discipline, location, and optional keyword.

    Args:
        jobtype (str): The type of job (e.g., 'internships').
        discipline (str, optional): The job discipline/category.
        location (str, optional): The job location.
        keyword (str, optional): Keyword to filter job titles.

    Returns:
        str: The constructed URL for the search query.
    """
    path = "/".join(p.strip("/") for p in (jobtype, discipline, location) if p)
    url  = f"https://au.gradconnection.com/{path}/"
    if keyword:
        url += f"?title={keyword}"
    return url

def add_page_param(base: str, page_no: int) -> str:
    """
    Add a page number parameter to a GradConnection search URL.

    Args:
        base (str): The base URL.
        page_no (int): The page number to append.

    Returns:
        str: The URL with the page parameter added.
    """
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}page={page_no}"

def scrape_job_detail(driver) -> dict:
    """
    Extract full job information from a GradConnection job detail page.

    Args:
        driver (selenium.webdriver): The Selenium WebDriver instance, already on the job detail page.

    Returns:
        dict: A dictionary containing all extracted job fields, including structured sections.

    This function is robust to variations in page structure and attempts to extract as much information as possible.
    """
    import re
    wait = WebDriverWait(driver, 10)
    time.sleep(1)  # Allow dynamic content to load

    def safe_text(selector, many=False):
        """
        Safely extract text or elements from the page using a CSS selector.
        Returns 'n/a' or [] on failure, depending on the 'many' flag.
        """
        try:
            if many:
                return driver.find_elements(By.CSS_SELECTOR, selector)
            return driver.find_element(By.CSS_SELECTOR, selector).text.strip()
        except:
            return [] if many else "n/a"

    # ─── basic fields ───
    title = safe_text("h1.employers-profile-h1")
    ai_summary = safe_text("div.ai-summary_campaign-summary-container")
    full_text_block = safe_text("div.campaign-content-container")
    posted_date = safe_text("span.hidden")
    closing_in = safe_text("span.job-info-header-closing-in")

    # ─── deeper extraction ───
    sections = {
        "overview": [],
        "responsibilities": [],
        "requirements": [],
        "skills_and_qualities": [],
        "salary_info": [],
        "about_company": [],
    }

    # Gather text elements for further parsing
    paragraphs = safe_text("div.campaign-content-container p", many=True)
    headings = safe_text("div.campaign-content-container h2", many=True)
    lists = safe_text("div.campaign-content-container ul, div.campaign-content-container ul.ak-ul", many=True)

    # Map possible heading text to normalized section keys
    section_mapping = {
        "about": "overview",
        "overview": "overview",
        "working at": "overview",
        "responsibilities": "responsibilities",
        "duties": "responsibilities",
        "tasks": "responsibilities",
        "objectives": "responsibilities",
        "qualifications": "requirements",
        "requirements": "requirements",
        "selection criteria": "requirements",
        "skills": "skills_and_qualities",
        "talents": "skills_and_qualities",
        "salary": "salary_info",
        "about company": "about_company",
        "about atlassian": "about_company",
        "perks & benefits": "about_company",
    }

    def map_heading(text):
        """
        Map a heading string to a section key using the section_mapping dictionary.
        Returns None if no match is found.
        """
        text = text.lower().strip()
        for key, value in section_mapping.items():
            if key in text:
                return value
        return None

    current_section = "overview"  # Default section if no headings found yet

    # Step through elements in order, assigning content to the correct section
    for elem in paragraphs + headings + lists:
        tag = elem.tag_name.lower()
        text = elem.text.strip()

        if not text:
            continue

        if tag.startswith("h"):
            maybe = map_heading(text)
            if maybe:
                current_section = maybe
            continue

        if tag == "p":
            sections[current_section].append(text)
            continue

        if tag == "ul":
            items = [li.text.strip() for li in elem.find_elements(By.TAG_NAME, "li")]
            sections[current_section].extend(items)

    return {
        "title": title,
        "posted_date": posted_date,
        "closing_in": closing_in,
        "ai_summary": ai_summary,
        "overview": sections["overview"],
        "responsibilities": sections["responsibilities"],
        "requirements": sections["requirements"],
        "skills_and_qualities": sections["skills_and_qualities"],
        "salary_info": sections["salary_info"],
        "about_company": sections["about_company"],
        "full_text": full_text_block
    }


# ───────────────────────────── scraper ────────────────────────────────────────
def get_jobs_full(jobtype:   str,
                  discipline: str | None = None,
                  location:   str | None = None,
                  keyword:    str | None = None,
                  max_pages:  int = 10,
                  headless:   bool = False,
                  debug:      bool = False) -> list[dict]:
    """
    Scrape all job listings from GradConnection search results, visiting each job page for full details.

    Args:
        jobtype (str): The type of job (e.g., 'internships').
        discipline (str, optional): The job discipline/category.
        location (str, optional): The job location.
        keyword (str, optional): Keyword to filter job titles.
        max_pages (int): Maximum number of result pages to scrape.
        headless (bool): Whether to run the browser in headless mode.
        debug (bool): If True, prints debug information.

    Returns:
        list[dict]: A list of dictionaries, each containing detailed job information.

    This function handles pagination, popups, and robustly collects all job links and their details.
    """
    base = build_url(jobtype, discipline, location, keyword)

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 10)

    seen, jobs = set(), []

    try:
        for page in range(1, max_pages + 1):
            url = base if page == 1 else add_page_param(base, page)
            driver.get(url)

            try:
                # Attempt to close any login popups that may block interaction
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                       "button.forcelogin-close-btn"))
                           ).click()
                time.sleep(0.4)
            except Exception:
                pass

            # Scroll to the bottom to ensure all jobs are loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            cards = driver.find_elements(By.CSS_SELECTOR, "div.campaign-box")
            if not cards:
                break

            for box in cards:
                try:
                    a = box.find_element(By.CSS_SELECTOR, "a.box-header-title")
                    link = a.get_attribute("href")
                    if link in seen:
                        continue
                    seen.add(link)

                    # Visit individual job page in a new tab
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(link)

                    job_detail = scrape_job_detail(driver)
                    job_detail["link"] = link

                    jobs.append(job_detail)

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    print(f"Error scraping job: {e}")
                    try:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except:
                        pass
                    continue

            print(f"[page {page}] collected {len(jobs)} jobs so far")

        return jobs

    finally:
        driver.quit()

def save_jobs_to_db(jobs, user_id, source="GradConnection"):
    """
    Save a list of scraped jobs to the database for a specific user and source.

    Args:
        jobs (list[dict]): The list of job dictionaries to save.
        user_id (int): The user ID to associate with the jobs.
        source (str): The source label for the jobs (default: 'GradConnection').

    This function first deletes any existing scraped jobs for the user/source, then inserts the new jobs.
    """
    from app.models import db, ScrapedJob
    import json
    # Delete existing scraped jobs for this user and source
    ScrapedJob.query.filter_by(user_id=user_id, source=source).delete()
    db.session.commit()
    for job in jobs:
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
            source=source
        )
        db.session.add(scraped_job)
    db.session.commit()

# ───────────────────────────── CLI example ────────────────────────────────────
if __name__ == "__main__":
    results = get_jobs_full(
        jobtype="internships",
        discipline="engineering-software",
        location="perth",
        keyword=None,
        max_pages=1,
        headless=True # False shows browser window while scraping
    )

    print(f"\nFound {len(results)} full jobs")
    print(json.dumps(results, indent=2, ensure_ascii=False))
