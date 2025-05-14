import unittest
from app.utils import fuzzy_search, resume_processor
from unittest.mock import patch, MagicMock

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
    def test_extract_text_from_pdf(self):
        # This test requires a sample PDF file in bytes. You can add a sample file for more robust testing.
        self.assertIsInstance(resume_processor.extract_text_from_pdf(b"%PDF-1.4\n%..."), str)

    def test_extract_text_from_docx(self):
        # This test requires a sample DOCX file in bytes. You can add a sample file for more robust testing.
        self.assertIsInstance(resume_processor.extract_text_from_docx(b"PK\x03\x04..."), str)

    def test_extract_text(self):
        # Test PDF
        self.assertIsInstance(resume_processor.extract_text(b"%PDF-1.4\n%...", "application/pdf"), str)
        # Test DOCX
        self.assertIsInstance(resume_processor.extract_text(b"PK\x03\x04...", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), str)
        # Test fallback
        self.assertEqual(resume_processor.extract_text(b"", "text/plain"), "")

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

if __name__ == '__main__':
    unittest.main() 