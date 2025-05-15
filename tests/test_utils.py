import unittest
from unittest.mock import patch, MagicMock
from app.utils import fuzzy_search, resume_processor, scraper_GC_jobs, scraper_GC_jobs_detailed

class TestFuzzySearch(unittest.TestCase):
    def test_is_fuzzy_match_exact(self):
        self.assertTrue(fuzzy_search.is_fuzzy_match('engineer', 'engineer'))
        self.assertFalse(fuzzy_search.is_fuzzy_match('engineer', 'doctor'))

    def test_is_fuzzy_match_fuzzy(self):
        self.assertTrue(fuzzy_search.is_fuzzy_match('engineer', 'engeneer', threshold=0.7))
        self.assertFalse(fuzzy_search.is_fuzzy_match('engineer', 'doctor', threshold=0.7))

    def test_job_matches_basic(self):
        class DummyJob:
            title = 'Software Engineer'
            ai_summary = 'Develops software.'
            overview = '[]'
            responsibilities = '[]'
            requirements = '[]'
            skills_and_qualities = '[]'
            salary_info = '[]'
            about_company = '["Tech Corp"]'
            full_text = 'Software engineering at Tech Corp.'

        job = DummyJob()
        self.assertTrue(fuzzy_search.job_matches(job, search='engineer'))
        self.assertFalse(fuzzy_search.job_matches(job, search='doctor'))

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
