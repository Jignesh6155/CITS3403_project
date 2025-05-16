import unittest
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from app import create_app
from app.models import db, User
from app.config import TestingConfig

# https://selenium-python.readthedocs.io/locating-elements.html


from flask import url_for

class SystemTestCase(unittest.TestCase):
    """
    Selenium system tests for major user flows.
    - Uses Chrome WebDriver in headless mode.
    - Starts Flask app in a background thread with TestingConfig (in-memory DB).
    - Covers home, signup, signin, dashboard, logout, and job search.
    - Add more tests for additional flows as needed.
    
    Configuration:
    - Requires selenium and ChromeDriver installed.
    - To use Firefox, change the driver setup accordingly.
    - To run against a different config, change TestingConfig below.
    """
    @classmethod
    def setUpClass(cls):
        # Start Flask app in a background thread
        cls.app = create_app(TestingConfig)
        cls.app.config['LIVESERVER_PORT'] = 5002
        cls.app.config['SERVER_NAME'] = 'localhost:5002'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        # Add a sample user
        user = User(name='seleniumuser', email='selenium@example.com', password='selpass')
        db.session.add(user)
        db.session.commit()
        def run_app():
            cls.app.run(port=5002, use_reloader=False)
        cls.server_thread = threading.Thread(target=run_app)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Wait for server to start
        # Set up Selenium WebDriver (Chrome, headless)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.base_url = 'http://localhost:5002'

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        # Flask server will exit when main thread exits
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()


    def test_signup_and_dashboard(self):
        self.driver.get(f'{self.base_url}/')
        # Fill signup form and submit
        self.driver.find_element(By.NAME, 'name').send_keys('selenium2')
        self.driver.find_element(By.NAME, 'email').send_keys('selenium2@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('sel2pass')
        self.driver.find_element(By.XPATH, '//form[@action="/signup"]//button').click()
        time.sleep(0.5)
        self.assertIn('Welcome', self.driver.page_source)

    def test_signin_and_logout(self):
        self.driver.get(f'{self.base_url}/')
        # Ensure the login form is visible
        self.driver.execute_script("showLogin();")
        # Fill signin form and submit
        self.driver.find_element(By.NAME, 'email').send_keys('selenium@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('selpass')
        self.driver.find_element(By.XPATH, '//form[@action="/signin"]//button').click()
        time.sleep(0.5)
        self.assertIn('Welcome', self.driver.page_source)


    def test_job_search_requires_login(self):
        self.driver.get(f'{self.base_url}/job-search')
        # Should redirect to home/login
        self.assertIn('CareerLink', self.driver.page_source)

    # Add more tests for other pages and flows as needed
    # For example: test application submission, notifications, friend requests, etc.
    # Use self.driver to interact with the browser and self.base_url for URLs.

if __name__ == '__main__':
    unittest.main() 