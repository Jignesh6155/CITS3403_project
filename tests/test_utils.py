import unittest
from unittest.mock import patch, MagicMock
from app.utils import fuzzy_search, resume_processor, scraper_GC_jobs_detailed

"""
Unit tests for utility functions in app.utils:
- fuzzy_search: tests fuzzy matching logic and job matching
- resume_processor: tests PDF/DOCX text extraction and OpenAI mock keyword extraction
- scraper_GC_jobs_detailed: tests URL building, pagination, and job scraping (mocked & integration)
"""

class TestFuzzySearch(unittest.TestCase):

    def test_is_fuzzy_match_realistic_cases(self):
        """Test is_fuzzy_match with realistic job title variations."""
        # Exact match
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Software Engineer'))

        # Common typo (fuzzy match expected to pass with low threshold)
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Sofware Enginer', threshold=0.7))

        # Case insensitivity
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'software engineer'))

        # Different job role (should fail)
        self.assertFalse(fuzzy_search.is_fuzzy_match('Software Engineer', 'Data Scientist', threshold=0.7))

        # Similar but slightly different roles
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Software Developer', threshold=0.6))

        # Too different, should fail
        self.assertFalse(fuzzy_search.is_fuzzy_match('Software Engineer', 'Doctor', threshold=0.6))

    def test_job_matches_with_realistic_job(self):
        """Test job_matches with a realistic job object and search terms."""
        class DummyJob:
            title = 'Backend Software Engineer'
            ai_summary = 'Work on backend systems and APIs.'
            overview = '[]'
            responsibilities = '[]'
            requirements = '[]'
            skills_and_qualities = '[]'
            salary_info = '[]'
            about_company = '["Tech Corp"]'
            full_text = 'This role involves backend development and software engineering tasks at Tech Corp.'

        job = DummyJob()

        # Should match on title
        self.assertTrue(fuzzy_search.job_matches(job, search='engineer'))

        # Should match on full_text content
        self.assertTrue(fuzzy_search.job_matches(job, search='backend'))

        # Should fail on irrelevant search
        self.assertFalse(fuzzy_search.job_matches(job, search='nurse'))


class TestResumeProcessor(unittest.TestCase):
    @patch('pypdf.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        # Mocking PDF reader's pages
        mock_reader_instance = mock_pdf_reader.return_value
        mock_reader_instance.pages = [MagicMock(extract_text=lambda: "Sample PDF text")]
        result = resume_processor.extract_text_from_pdf(b"dummy bytes")
        self.assertIn("Sample PDF text", result)

    @patch('docx2txt.process', return_value="Sample DOCX text")
    def test_extract_text_from_docx(self, mock_docx_process):
        result = resume_processor.extract_text_from_docx(b"dummy bytes")
        self.assertIn("Sample DOCX text", result)

    @patch('app.utils.resume_processor.openai.OpenAI')
    def test_extract_keywords_openai(self, mock_openai):
        # Mock OpenAI API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Engineer, Developer, Analyst, Consultant, Manager, Software"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = resume_processor.extract_keywords_openai("resume text", api_key="fake")
        self.assertIn("Engineer", result)
        self.assertIn("Software", result)


class TestScraperGCJobsDetailed(unittest.TestCase):
    def test_build_url(self):
        url = scraper_GC_jobs_detailed.build_url('internships', 'engineering', 'perth', 'ai')
        self.assertIn('internships', url)
        self.assertIn('engineering', url)
        self.assertIn('perth', url)
        self.assertIn('title=ai', url)

    def test_add_page_param(self):
        url = scraper_GC_jobs_detailed.add_page_param('https://test.com', 2)
        self.assertIn('page=2', url)
        url2 = scraper_GC_jobs_detailed.add_page_param('https://test.com?foo=bar', 3)
        self.assertIn('&page=3', url2)

    @patch('app.utils.scraper_GC_jobs_detailed.webdriver.Chrome')
    def test_get_jobs_full_mocked(self, mock_chrome):
        """Unit test with webdriver Chrome mocked (no real browser)."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []
        jobs = scraper_GC_jobs_detailed.get_jobs_full('internships', max_pages=1, headless=True)
        self.assertIsInstance(jobs, list)
        self.assertEqual(len(jobs), 0)

    def test_get_jobs_full_integration(self):
        """Integration test with real browser (headless=False)"""
        jobs = scraper_GC_jobs_detailed.get_jobs_full(
            jobtype='internships',
            discipline='engineering',
            location='perth',
            keyword='ai',
            max_pages=1,
            headless=False  # Show the browser window
        )
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "Expected at least one job to be scraped")

        job = jobs[0]
        self.assertIn("title", job)
        self.assertIn("link", job)
        self.assertTrue(job["title"])
        self.assertTrue(job["link"])

if __name__ == '__main__':
    unittest.main()
