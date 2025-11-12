# 42 Intra Utilities

Python utilities for accessing 42 school resources through the official API and web interface. Provides clean interfaces to both api.intra.42.fr (OAuth2) and projects.intra.42.fr (web scraping).

## Features

- **OAuth2 API Client** - Clean wrapper around the 42 Intra API with automatic token management
- **Web Scraper** - Access project subjects and attachments from the projects website
- **Pagination Support** - Efficiently handle large datasets with generator-based iteration
- **Progress Tracking** - Optional progress bars for downloads
- **Smart Downloads** - Automatic timeouts and context manager support

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

# Get all projects
projects = scraper.get_projects()
print(f"Found {len(projects)} projects")

# Get attachments for a specific project
project = next((p for p in projects if p['name'] == 'libft'), None)
if project:
    attachments = scraper.get_project_attachments(project['url'])
    for url in attachments:
        filename = url.split('/')[-1]
        scraper.download_attachment(url, f'downloads/{filename}')
```

**Your implementation should include:**
- Progress tracking (using `tqdm`)
- Error handling and retries
- Rate limiting (add `time.sleep()` between requests)
- Graceful interruption (signal handling)

See `examples/scraper_example.py` for a template.

### Interactive Experimentation

Use the Jupyter notebook for exploring HTML structure:

```bash
jupyter notebook scraper_experiment.ipynb
```

## Architecture

### Core Components

- **`intra42.py`** - Library with two main classes:
  - `IntraAPI` - OAuth2 client for API access
  - `IntraScrape` - Web scraper for project subjects

- **`test_intra42.py`** - Comprehensive test suite

- **`scraper_experiment.ipynb`** - Interactive notebook for HTML exploration

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
user = api.get('/v2/users/tfregni')

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

### Basic Scraping

```python
from intra42 import IntraScrape
import os

cookies = {
    '_intra_42_session_production': os.getenv('SESSION_COOKIE'),
    'cf_clearance': os.getenv('CF_CLEARANCE_COOKIE'),
    'user.id': os.getenv('USER_ID_COOKIE')
}

scraper = IntraScrape(cookies)

# Get all projects
projects = scraper.get_projects()

# Get attachments for a specific project
attachments = scraper.get_project_attachments('/projects/42cursus-libft')

# Download files
for url in attachments:
    filename = url.split('/')[-1]
    scraper.download_attachment(url, f'downloads/{filename}')
```

### Find Project by Name

```python
# Search for project URL by name
project_url = scraper.get_project_url_by_name('libft')
if project_url:
    attachments = scraper.get_project_attachments(project_url)
```

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
├── scraper_experiment.ipynb # Interactive notebook for HTML exploration
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

## Future Improvements

Potential enhancements for the library:

- **Logging System**: Replace `print()` statements with Python's `logging` module for better control
- **Token Expiration Tracking**: Automatically refresh OAuth2 tokens before they expire
- **Retry Logic**: Built-in exponential backoff for failed requests
- **Session Persistence**: Save and restore session state
- **Async Support**: Add async variants of API calls using `aiohttp`
- **CLI Tool**: Command-line interface for common operations

Contributions are welcome!

## Contributing

Feel free to submit issues or pull requests!

## Disclaimer

This library is for educational purposes. Respect 42's terms of service and be considerate with your usage. Users are responsible for how they use these utilities.

## License

MIT License - See LICENSE file for details

## Author

Created by a 42 Berlin student to streamline access to 42 resources.
