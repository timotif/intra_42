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
    Example: Download attachments for a single project with versioning

    Args:
        project_name: Name of the project to scrape
    """
    scraper = IntraScrape(get_cookies())

    # Get all projects (parallel by default, ~16x faster)
    # Optional: parallel=False for sequential mode
    # Optional: max_workers=4 to customize thread count
    projects = scraper.get_all_projects()

    # Find the specific project
    # TODO: Add your own search/filter logic
    # Hint: Use get_project_url_by_name() or get_projects_to_scrape()

    # Get attachments
    # TODO: Implement attachment download logic with versioning
    # Example pattern:
    #
    # attachments = scraper.get_project_attachments(project_url)
    # for url in attachments:
    #     filename = url.split('/')[-1]
    #     base_path = f'downloads/{filename}'
    #
    #     # Smart versioned download
    #     actual_path, should_download = scraper.get_versioned_filepath(url, base_path)
    #     if should_download:
    #         scraper.download_attachment(url, actual_path)
    #         # File saved with timestamp if it's an update:
    #         # downloads/file.pdf or downloads/file_20250509_141612.pdf
    #     else:
    #         # File already up-to-date, skipped

    pass  # Replace with your implementation


# TODO: Implement your own main function
def main():
    """
    Your scraping implementation goes here.

    Consider:
    - Rate limiting (time.sleep() between requests)
    - Error handling and retries
    - Progress tracking (tqdm is already available)
    - Graceful interruption (signal handling for Ctrl+C)
    - Batch operations with get_projects_to_scrape()

    Library features available:
    - Parallel pagination (default, auto-detected workers)
    - Versioned downloads (preserves old files)
    - Smart skip logic (only downloads updates)
    - Remote timestamp checking (HTTP HEAD requests)
    """
    pass  # Replace with your implementation


if __name__ == "__main__":
    # TODO: Implement your usage
    print("This is a template. Implement your own scraping logic.")
    print("See README.md for examples of how to use IntraScrape.")
    print("\nNew features:")
    print("  - Parallel pagination (10-16x faster)")
    print("  - Versioned downloads (preserves old files)")
    print("  - Smart updates (only downloads changes)")
