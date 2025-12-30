"""
Example: How to scrape 42 project subjects

This is a template showing how to use the IntraScrape class.
Users must understand and customize this code for their own use.
"""

from dotenv import load_dotenv
import os
from intra42 import IntraScrape

# TODO: Implement your own cookie extraction
def get_cookies():
    """
    Extract your session cookies from the browser.

    Steps:
    1. Login to projects.intra.42.fr
    2. Open DevTools (F12) → Application → Cookies
    3. Copy the values for required cookies
    """
    load_dotenv()

    # TODO: Add your cookies to .env and load them here
    cookies = {
        '_intra_42_session_production': os.getenv('SESSION_COOKIE'),
        'cf_clearance': os.getenv('CF_CLEARANCE_COOKIE'),
        'user.id': os.getenv('USER_ID_COOKIE')
    }

    return cookies


# TODO: Implement your own scraping logic
def scrape_single_project(project_name: str):
    """
    Example: Download attachments for a single project

    Args:
        project_name: Name of the project to scrape
    """
    scraper = IntraScrape(get_cookies())

    # Get all projects
    projects = scraper.get_all_projects()

    # Find the specific project
    # TODO: Add your own search/filter logic

    # Get attachments
    # TODO: Implement attachment download logic

    pass  # Replace with your implementation


# TODO: Implement your own main function
def main():
    """
    Your scraping implementation goes here.

    Consider:
    - Rate limiting (time.sleep() between requests)
    - Error handling
    - Progress tracking
    - Graceful interruption (Ctrl+C)
    """
    pass  # Replace with your implementation


if __name__ == "__main__":
    # TODO: Implement your usage
    print("This is a template. Implement your own scraping logic.")
    print("See README.md for examples of how to use IntraScrape.")
