# 42 Intra Utilities

Python utilities for accessing 42 school resources through the official API and web interface. Provides clean interfaces to both api.intra.42.fr (OAuth2) and projects.intra.42.fr (web scraping).

## Features

- **OAuth2 API Client** - Clean wrapper around the 42 Intra API with automatic token management
- **Web Scraper** - Access project subjects and attachments from the projects website
- **Versioned Downloads** - Automatic file versioning with timestamp tracking, preserves old versions
- **Parallel Pagination** - Multi-threaded page fetching with auto-detected worker count (16x faster)
- **Smart Downloads** - Skip unchanged files, only download updates
- **Pagination Support** - Efficiently handle large datasets with generator-based iteration
- **Progress Tracking** - Optional progress bars for downloads

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd intra_42
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (see [Configuration](#configuration))

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
############################
# 42 Intra API Credentials #
############################
INTRA_UID=your-uid-here
INTRA_SECRET=your-secret-here

############################
# 42 Intra Cookies         #
############################
SESSION_COOKIE=your-session-cookie
USER_ID_COOKIE=your-user-id
CF_CLEARANCE_COOKIE=your-cf-clearance
```

### Getting API Credentials

1. Go to [42 API Applications](https://profile.intra.42.fr/oauth/applications)
2. Create a new application
3. Copy the `UID` and `SECRET` to your `.env` file

### Getting Session Cookies

1. Login to [projects.intra.42.fr](https://projects.intra.42.fr)
2. Open Browser DevTools (F12)
3. Go to **Application** → **Cookies** → `https://projects.intra.42.fr`
4. Copy these cookie values to `.env`:
   - `_intra_42_session_production` → `SESSION_COOKIE`
   - `user.id` → `USER_ID_COOKIE`
   - `cf_clearance` → `CF_CLEARANCE_COOKIE`

**Note:** Session cookies expire periodically and need to be refreshed.

## Usage

**Important**: This repository provides core library classes only. Users must write their own implementation scripts. This ensures you understand what your code is doing and take responsibility for your usage.

See `examples/` directory for templates and the sections below for usage patterns.

### API Usage - Fetching Data

```python
from intra42 import IntraAPI
import os

# Initialize API client
api = IntraAPI(
    os.getenv('INTRA_UID'),
    os.getenv('INTRA_SECRET')
)

# Get campus info
campus = api.get('/v2/campus/51')  # Berlin campus

# Get users with pagination
users_page_1 = api.get('/v2/campus/51/users', page=1, page_size=100)

# Get all users across all pages
all_users = api.get_all_pages('/v2/campus/51/users')

# Memory-efficient iteration
for user in api.get_paginated('/v2/campus/51/users'):
    print(user['login'])
```

### Web Scraping Usage - Accessing Projects

```python
from intra42 import IntraScrape
import os

# Setup cookies from environment
cookies = {
    '_intra_42_session_production': os.getenv('SESSION_COOKIE'),
    'cf_clearance': os.getenv('CF_CLEARANCE_COOKIE'),
    'user.id': os.getenv('USER_ID_COOKIE')
}

scraper = IntraScrape(cookies)

# Get all projects (parallel by default, ~16x faster than sequential)
projects = scraper.get_all_projects()
print(f"Found {len(projects)} projects")

# Sequential mode (if needed)
projects = scraper.get_all_projects(parallel=False)

# Custom worker count
projects = scraper.get_all_projects(parallel=True, max_workers=4)

# Get specific projects by name
scraper.get_projects_to_scrape(['libft', 'ft_printf'])

# Get attachments for a specific project
project = next((p for p in projects if p['name'] == 'libft'), None)
if project:
    attachments = scraper.get_project_attachments(project['url'])
    for url in attachments:
        filename = url.split('/')[-1]
        base_path = f'downloads/{filename}'

        # Smart versioned download
        actual_path, should_download = scraper.get_versioned_filepath(url, base_path)
        if should_download:
            scraper.download_attachment(url, actual_path)
        # Files automatically versioned: file.pdf -> file_20250509_141612.pdf
```

**Features demonstrated:**
- Parallel pagination (automatic worker detection)
- Versioned downloads (preserves old files)
- Smart skip logic (only downloads updates)
- Progress tracking (built-in with `tqdm`)

**Your implementation should include:**
- Error handling and retries
- Rate limiting (add `time.sleep()` between requests)
- Graceful interruption (signal handling)

See `examples/scraper_example.py` for a complete template.

## Architecture

### Core Components

- **`intra42.py`** - Library with two main classes:
  - `IntraAPI` - OAuth2 client for API access
  - `IntraScrape` - Web scraper for project subjects

- **`test_intra42.py`** - Comprehensive test suite

- **`examples/`** - Template scripts showing how to use the library
  - `scraper_example.py` - Template for custom implementations

### Authentication

Two separate authentication mechanisms:

| Type | Used For | Credentials | Expiration |
|------|----------|-------------|------------|
| OAuth2 | API (api.intra.42.fr) | `INTRA_UID`, `INTRA_SECRET` | ~2 hours (auto-refreshed) |
| Cookies | Web (projects.intra.42.fr) | Session cookies | Varies (manual refresh) |

## API Examples

### Basic Requests

```python
from intra42 import IntraAPI

api = IntraAPI('your_uid', 'your_secret')

# Get user profile
user = api.get('/v2/users/<user>')

# Get project details
project = api.get('/v2/projects/1314')  # libft

# Get cursus info
cursus = api.get('/v2/cursus/21')  # 42cursus
```

### Pagination Patterns

```python
# Manual pagination
for page in range(1, 10):
    users = api.get('/v2/campus/51/users', page=page, page_size=100)
    process(users)

# Automatic pagination (generator - memory efficient)
for user in api.get_paginated('/v2/campus/51/users', page_size=100):
    process(user)

# All at once (convenience method)
all_users = api.get_all_pages('/v2/campus/51/users', page_size=100)
```

## Web Scraping Examples

### Basic Scraping with Versioning

```python
from intra42 import IntraScrape
import os

cookies = {
    '_intra_42_session_production': os.getenv('SESSION_COOKIE'),
    'cf_clearance': os.getenv('CF_CLEARANCE_COOKIE'),
    'user.id': os.getenv('USER_ID_COOKIE')
}

scraper = IntraScrape(cookies)

# Get all projects (uses parallel pagination by default)
projects = scraper.get_all_projects()  # ~15s for 334 projects

# Get attachments for a specific project
attachments = scraper.get_project_attachments('/projects/42cursus-libft')

# Download with automatic versioning
for url in attachments:
    filename = url.split('/')[-1]
    base_path = f'downloads/{filename}'

    # Check if file needs updating
    actual_path, should_download = scraper.get_versioned_filepath(url, base_path)

    if should_download:
        scraper.download_attachment(url, actual_path)
        print(f"Downloaded: {actual_path}")
    else:
        print(f"Skipped: {actual_path} (already up-to-date)")
```

### Parallel vs Sequential Pagination

```python
# Parallel mode (default) - auto-detects optimal workers
projects = scraper.get_all_projects()
# Fetching 17 pages in parallel with 32 workers...
# Total projects loaded: 334 (~15 seconds)

# Sequential mode - useful for debugging or rate limit concerns
projects = scraper.get_all_projects(parallel=False)
# Fetching 17 pages sequentially...
# Loaded page 1/17: 20 projects
# ... (~240 seconds)

# Custom worker count
projects = scraper.get_all_projects(parallel=True, max_workers=4)
```

### Find and Filter Projects

```python
# Search for project URL by name
project_url = scraper.get_project_url_by_name('libft')
if project_url:
    attachments = scraper.get_project_attachments(project_url)

# Get specific projects by name list
scraper.get_projects_to_scrape(['libft', 'ft_printf', 'minishell'])
for project in scraper.projects_to_scrape:
    print(f"Processing: {project['name']}")
```

### File Versioning Behavior

When a remote file is updated, the scraper creates a versioned copy:

```
downloads/
├── en.subject.pdf              # Original (downloaded 2024-01-15)
└── en.subject_20250509_141612.pdf  # Update (remote modified 2025-05-09 14:16:12)
```

- First download: Uses base filename (`en.subject.pdf`)
- Subsequent updates: Adds timestamp from remote `Last-Modified` header
- Old versions preserved automatically
- Timestamp in filename reflects when file was **last modified on server**, not download time

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_intra42.py -v

# Run specific test class
pytest test_intra42.py::TestIntraAPI -v

# Run with coverage
pytest test_intra42.py --cov=intra42 --cov-report=html
```

## Project Structure

```
intra_42/
├── intra42.py              # Core library (IntraAPI + IntraScrape classes)
├── test_intra42.py         # Test suite
├── examples/
│   └── scraper_example.py  # Template for building your own scripts
├── requirements.txt        # Dependencies
├── .env                    # Configuration (not in git, create from .env.example)
├── .env.example            # Configuration template
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

**Note**: Implementation scripts are intentionally not included in the repository. Users must write their own scripts using the provided library classes. This ensures you understand the code you're running and take responsibility for your usage.

## Error Handling

The library classes provide basic error handling:

- **Network failures**: 30-second timeout on downloads
- **HTTP errors**: Raises exceptions with status codes
- **Invalid responses**: JSONDecodeError on malformed API responses
- **Missing elements**: Returns empty lists/None for missing HTML elements

**Your implementation should add:**
- Retry logic for failed requests
- Graceful degradation
- User-friendly error messages
- Logging

## Best Practices

1. **Rate Limiting**: Be respectful of the 42 infrastructure
   ```python
   import time
   for project in projects:
       process_project(project)
       time.sleep(1)  # 1 second between requests
   ```

2. **Cookie Refresh**: Session cookies expire - re-extract if requests start failing

3. **Error Handling**: Implement proper try/except blocks around network calls

## Troubleshooting

### "Failed to retrieve projects: 403"
- Your session cookies have expired
- Re-extract cookies from your browser

### "Invalid client credentials"
- Check `INTRA_UID` and `INTRA_SECRET` in `.env`
- Verify your API application is active

### "No attachments found"
- Some projects genuinely have no attachments
- Check if you can see them in the browser

### Downloads hang
- Check your internet connection
- 30-second timeout will trigger automatically

## Campus IDs

Common campus IDs for API queries:

| Campus | ID |
|--------|------|
| Berlin | 51 |
| Paris | 1 |
| Madrid | 22 |
| Amsterdam | 14 |
| Singapore | 64 |

Find more: `api.get('/v2/campus')`

## Robots.txt Compliance

This library respects web scraping standards and has been verified against robots.txt:

### Compliance Status

✅ **projects.intra.42.fr/robots.txt** - No active restrictions (all `Disallow` directives are commented out)
✅ **api.intra.42.fr/robots.txt** - No active restrictions, publicly accessible API

### Responsible Usage

While robots.txt permits access, implement responsible practices:

- **Authenticated Access**: Uses your personal session cookies (accessing content you have legitimate access to)
- **Rate Limiting**: Add delays between requests to avoid overwhelming servers
- **Graceful Interruption**: Implement proper Ctrl+C handling
- **Smart Resume**: Check if files exist before downloading
- **Timeout Handling**: 30-second timeouts prevent hanging connections

### Ethical Considerations

- **Purpose**: Personal use of educational materials you have access to
- **Scope**: Only access content you're authorized to view
- **Impact**: Minimize server load with rate limiting
- **Transparency**: Open source with clear documentation

**Note**: robots.txt compliance does not supersede 42's Terms of Service. Use this library responsibly as an authorized 42 student.

## Performance Notes

### Parallel Pagination

The library supports parallel page fetching with auto-detected worker count:

```python
# Auto-detect: min(32, cpu_count * 2) for I/O-bound tasks
projects = scraper.get_all_projects()  # Parallel by default

# Customize workers
projects = scraper.get_all_projects(max_workers=4)
```

On a typical machine, parallel mode is **10-16x faster** than sequential for fetching multiple pages.

### Smart Downloads

The versioning system uses HTTP HEAD requests to check file timestamps before downloading:

- Only downloads files that are new or updated
- Preserves bandwidth and time on re-runs
- Typical skip rate: 90%+ when most files unchanged

## Future Improvements

Potential enhancements for the library:

- **Logging System**: Replace `print()` statements with Python's `logging` module for better control
- **Token Expiration Tracking**: Automatically refresh OAuth2 tokens before they expire
- **Retry Logic**: Built-in exponential backoff for failed requests
- **Session Persistence**: Save and restore session state
- **Async Support**: Add async variants of API calls using `aiohttp`
- **Compression Detection**: Track file hashes for content-based versioning

Contributions are welcome!

## Contributing

Feel free to submit issues or pull requests!

## Disclaimer

This library is for educational purposes. Respect 42's terms of service and be considerate with your usage. Users are responsible for how they use these utilities.

## License

MIT License - See LICENSE file for details

## Author

Created by a 42 Berlin student to streamline access to 42 resources.
