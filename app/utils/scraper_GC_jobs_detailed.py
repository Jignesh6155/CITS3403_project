from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json

# ───────────────────────────── helpers ────────────────────────────────────────
def build_url(jobtype: str, discipline: str | None = None, location: str | None = None, keyword: str | None = None) -> str:
    path = "/".join(p.strip("/") for p in (jobtype, discipline, location) if p)
    url  = f"https://au.gradconnection.com/{path}/"
    if keyword:
        url += f"?title={keyword}"
    return url

def add_page_param(base: str, page_no: int) -> str:
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}page={page_no}"

def scrape_job_detail(driver) -> dict:
    """
    Extract full job info from GradConnection job pages, handling all variations seen so far.
    """
    import re
    wait = WebDriverWait(driver, 10)
    time.sleep(1)

    def safe_text(selector, many=False):
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

    # Gather text elements
    paragraphs = safe_text("div.campaign-content-container p", many=True)
    headings = safe_text("div.campaign-content-container h2", many=True)
    lists = safe_text("div.campaign-content-container ul, div.campaign-content-container ul.ak-ul", many=True)

    # Map headings to normalized labels
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

    # Helper to map a heading into one of our section keys
    def map_heading(text):
        text = text.lower().strip()
        for key, value in section_mapping.items():
            if key in text:
                return value
        return None

    current_section = "overview"  # Default if no headings found yet

    # Step through elements in order
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
                  headless:   bool = False) -> list[dict]:
    """
    Navigate through the search results, collect each job link, visit and scrape all job information.
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
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                       "button.forcelogin-close-btn"))
                           ).click()
                time.sleep(0.4)
            except Exception:
                pass

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

                    # Visit individual job page
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

# ───────────────────────────── CLI example ────────────────────────────────────
if __name__ == "__main__":
    results = get_jobs_full(
        jobtype="internships",
        discipline="engineering-software",
        location="perth",
        keyword=None,
        max_pages=2,
        headless=False
    )

    print(f"\nFound {len(results)} full jobs")
    print(json.dumps(results, indent=2, ensure_ascii=False))
