"""
Utility function tests for Flask application.

This module contains tests for the utility functions in app.utils package,
including fuzzy search, resume processing, and job scraping utilities.
It verifies both unit-level functionality (with mocks) and integration-level
functionality with external components.
"""

import unittest
from unittest.mock import patch, MagicMock
from app.utils import fuzzy_search, resume_processor, scraper_GC_jobs, scraper_GC_jobs_detailed

class TestFuzzySearch(unittest.TestCase):
    """
    Tests for the fuzzy search utility functions.
    
    This test suite verifies the string matching and job filtering capabilities
    of the fuzzy_search utility, ensuring it can correctly identify similar strings
    and match jobs based on search criteria with appropriate thresholds.
    """

    def test_is_fuzzy_match_realistic_cases(self):
        """
        Test fuzzy matching with realistic job title variations.
        
        Verifies that the fuzzy matching algorithm correctly:
        - Matches exact strings
        - Handles common typos/misspellings
        - Maintains case insensitivity
        - Distinguishes between sufficiently different strings
        - Identifies similar job titles with appropriate thresholds
        """
        # Exact match should always pass
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Software Engineer'))

        # Common typo (fuzzy match expected to pass with low threshold)
        # Tests handling of simple character omissions
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Sofware Enginer', threshold=0.7))

        # Case insensitivity verification
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'software engineer'))

        # Different job role (should fail - verifies discrimination capability)
        self.assertFalse(fuzzy_search.is_fuzzy_match('Software Engineer', 'Data Scientist', threshold=0.7))

        # Similar but slightly different roles - should pass with lower threshold
        self.assertTrue(fuzzy_search.is_fuzzy_match('Software Engineer', 'Software Developer', threshold=0.6))

        # Completely different strings - should fail even with low threshold
        self.assertFalse(fuzzy_search.is_fuzzy_match('Software Engineer', 'Doctor', threshold=0.6))

    def test_job_matches_with_realistic_job(self):
        """
        Test job matching with realistic job object attributes.
        
        Creates a dummy job object with typical attributes and verifies
        that the job_matches function correctly identifies matching terms
        across different fields of the job record.
        """
        # Create dummy job class with typical attributes
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

        # Should match on title field
        self.assertTrue(fuzzy_search.job_matches(job, search='engineer'))

        # Should match on full_text content (different field)
        self.assertTrue(fuzzy_search.job_matches(job, search='backend'))

        # Should fail on irrelevant search term (negative test)
        self.assertFalse(fuzzy_search.job_matches(job, search='nurse'))


class TestResumeProcessor(unittest.TestCase):
    """
    Tests for resume processing utilities.
    
    This test suite verifies the functionality of resume processing utilities,
    including text extraction from different document formats (PDF, DOCX)
    and keyword extraction using AI services.
    """
    
    @patch('pypdf.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """
        Test PDF text extraction functionality.
        
        Uses mocking to verify that the PDF extraction function correctly
        processes PDF documents and extracts text content.
        """
        # Set up mock PDF reader to return predictable content
        mock_reader_instance = mock_pdf_reader.return_value
        mock_reader_instance.pages = [MagicMock(extract_text=lambda: "Sample PDF text")]
        
        # Test extraction function with dummy binary data
        result = resume_processor.extract_text_from_pdf(b"dummy bytes")
        self.assertIn("Sample PDF text", result)

    @patch('docx2txt.process', return_value="Sample DOCX text")
    def test_extract_text_from_docx(self, mock_docx_process):
        """
        Test DOCX text extraction functionality.
        
        Uses mocking to verify that the DOCX extraction function correctly
        processes Word documents and extracts text content.
        """
        # Test extraction with mocked docx2txt processor
        result = resume_processor.extract_text_from_docx(b"dummy bytes")
        self.assertIn("Sample DOCX text", result)

    @patch('app.utils.resume_processor.openai.OpenAI')
    def test_extract_keywords_openai(self, mock_openai):
        """
        Test keyword extraction using OpenAI API.
        
        Uses mocking to verify that the keyword extraction function correctly
        processes text content and extracts relevant keywords using the OpenAI API.
        """
        # Set up mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Simulate API response with predictable keywords
        mock_response.choices = [MagicMock(message=MagicMock(
            content="Engineer, Developer, Analyst, Consultant, Manager, Software"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Test keyword extraction
        result = resume_processor.extract_keywords_openai("resume text", api_key="fake")
        # Verify expected keywords are present
        self.assertIn("Engineer", result)
        self.assertIn("Software", result)


class TestScraperGCJobsDetailed(unittest.TestCase):
    """
    Tests for GradConnection job scraping utilities.
    
    This test suite verifies the functionality of job scraping utilities,
    including URL construction, pagination handling, and job data extraction.
    It includes both unit tests with mocks and integration tests with actual
    web interactions.
    """
    
    def test_build_url(self):
        """
        Test URL building for job search parameters.
        
        Verifies that the URL builder correctly incorporates job type,
        discipline, location, and keyword parameters into the search URL.
        """
        url = scraper_GC_jobs_detailed.build_url('internships', 'engineering', 'perth', 'ai')
        # Verify each parameter is correctly included in the URL
        self.assertIn('internships', url)  # Job type
        self.assertIn('engineering', url)  # Discipline
        self.assertIn('perth', url)        # Location
        self.assertIn('title=ai', url)     # Search keyword

    def test_add_page_param(self):
        """
        Test pagination parameter handling.
        
        Verifies that the pagination function correctly adds page parameters
        to URLs, handling both clean URLs and URLs with existing parameters.
        """
        # Test adding page to URL with no existing parameters
        url = scraper_GC_jobs_detailed.add_page_param('https://test.com', 2)
        self.assertIn('page=2', url)
        
        # Test adding page to URL with existing parameters
        url2 = scraper_GC_jobs_detailed.add_page_param('https://test.com?foo=bar', 3)
        self.assertIn('&page=3', url2)  # Should use & connector for additional param

    @patch('app.utils.scraper_GC_jobs_detailed.webdriver.Chrome')
    def test_get_jobs_full_mocked(self, mock_chrome):
        """
        Test job scraping with mocked browser.
        
        Uses mocking to verify that the job scraping function correctly
        processes browser interactions and handles empty results.
        """
        # Set up mock Chrome driver with empty job results
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []  # No jobs found
        
        # Test job scraping function
        jobs = scraper_GC_jobs_detailed.get_jobs_full('internships', max_pages=1, headless=True)
        
        # Verify results structure even with empty data
        self.assertIsInstance(jobs, list)
        self.assertEqual(len(jobs), 0)  # Should return empty list

    def test_get_jobs_full_integration(self):
        """
        Test job scraping with actual browser integration.
        
        Performs an actual web scraping test (non-mocked) to verify the full
        job scraping workflow with real data. This test may require internet
        connection and can be longer-running.
        """
        # Configure scraping with specific parameters for reproducible results
        jobs = scraper_GC_jobs_detailed.get_jobs_full(
            jobtype='internships',
            discipline='engineering',
            location='perth',
            keyword='ai',
            max_pages=1,       # Limit to first page for testing speed
            headless=False     # Show the browser window for debugging
        )
        
        # Verify results contain expected structure and data
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "Expected at least one job to be scraped")

        # Verify first job has required attributes
        job = jobs[0]
        self.assertIn("title", job)  # Should have title
        self.assertIn("link", job)   # Should have link
        self.assertTrue(job["title"])  # Title should be non-empty
        self.assertTrue(job["link"])   # Link should be non-empty

if __name__ == '__main__':
    unittest.main()
