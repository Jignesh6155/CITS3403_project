"""
Minimal GradConnection scraper
──────────────────────────────
• Build the search-URL from the four optional inputs  
• Page through the result-set (stops when no cards or max_pages reached)  
• Extract every job-card:  *title  ·  link  ·  closing interval*  

Inputs
------
jobtype     “internships”, “graduate-jobs”, “entry-level-jobs”… (no default)  
discipline  e.g. “engineering-software” (optional)  
location    e.g. “perth”                (optional)  
keyword     e.g. “fpga”                 (optional)  → adds ?title=keyword  
max_pages   how many result pages to walk through        (default = 10)  
headless    run Chrome invisibly                           (default = False)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json


# ───────────────────────────── helpers ────────────────────────────────────────
def build_url(jobtype: str,
              discipline: str | None = None,
              location:   str | None = None,
              keyword:    str | None = None) -> str:
    """
    Assemble the GradConnection URL while omitting any empty / None segment.
    Pattern:  https://au.gradconnection.com/<jobtype>/<discipline>/<location>/?title=<keyword>
    """
    # keep only non-blank path pieces
    path = "/".join(p.strip("/") for p in (jobtype, discipline, location) if p)
    url  = f"https://au.gradconnection.com/{path}/"
    if keyword:                         # only add the query-string when needed
        url += f"?title={keyword}"
    return url


def add_page_param(base: str, page_no: int) -> str:
    """
    GradConnection uses  …?page=N     if no query-string yet, otherwise …&page=N
    """
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}page={page_no}"


# ───────────────────────────── scraper ────────────────────────────────────────
def get_jobs(jobtype:   str,
             discipline: str | None = None,
             location:   str | None = None,
             keyword:    str | None = None,
             max_pages:  int = 10,
             headless:   bool = True,
             debug:      bool = False) -> list[dict]:
    """
    Navigate through the search results and harvest every <div class="campaign-box">.
    """
    base = build_url(jobtype, discipline, location, keyword)

    # Selenium browser setup ---------------------------------------------------
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=opts)
    wait   = WebDriverWait(driver, 10)

    seen, jobs = set(), []

    try:
        for page in range(1, max_pages + 1):
            url = base if page == 1 else add_page_param(base, page)
            driver.get(url)

            # close the login / sign-up modal if it pops up --------------------
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                       "button.forcelogin-close-btn"))
                           ).click()
                time.sleep(0.4)
            except Exception:
                pass

            # scroll to lift GC's lazy-load height cap -------------------------
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)

            cards = driver.find_elements(By.CSS_SELECTOR, "div.campaign-box")
            if not cards:              # no more results → stop early
                break

            for box in cards:
                try:
                    a    = box.find_element(By.CSS_SELECTOR, "a.box-header-title")
                    link = a.get_attribute("href")
                    if link in seen:    # skip duplicates across pages
                        continue
                    seen.add(link)

                    try:                # "Closing in ..." text may be absent
                        closing = box.find_element(
                            By.CSS_SELECTOR, "div.box-closing-interval span"
                        ).text.strip()
                    except Exception:
                        closing = "n/a"

                    jobs.append({
                        "title":   a.text.strip(),
                        "link":    link,
                        "closing": closing
                    })
                except Exception:
                    continue

            if debug:
                print(f"[page {page}] collected {len(cards)} cards "
                      f"({len(jobs)} total)")

        return jobs

    finally:
        driver.quit()


# ───────────────────────────── CLI example ────────────────────────────────────
if __name__ == "__main__":
    """
    Example: internships → engineering-software → perth → keyword "fpga"
    Change the arguments or call `get_jobs()` directly from other code.
    """
    results = get_jobs(
        jobtype="internships",
        discipline="engineering-software",
        location="perth",
        keyword=None,
        max_pages=3,           # scrape up to 3 pages
        headless=True,         # set to False to watch the browser work
        debug=True
    )

    print(f"\nFound {len(results)} unique jobs")
    print(json.dumps(results, indent=2, ensure_ascii=False))


