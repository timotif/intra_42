# 42 Intra Archiver

A Python tool for archiving 42 school project subjects and campus data using both the official 42 Intra API and web scraping.

## Features

- **OAuth2 API Client** - Access 42 Intra API (api.intra.42.fr) with automatic token management
- **Web Scraper** - Download project subjects and attachments from projects.intra.42.fr
- **Progress Tracking** - Beautiful nested progress bars with download speeds
- **Graceful Interruption** - Ctrl+C handling for safe exits
- **Smart Resume** - Skips already downloaded files
- **Pagination Support** - Efficiently handles large datasets

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd api_login
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

**Important**: This repository provides the core classes (`IntraAPI` and `IntraScrape`) as libraries. Users must write their own scripts to use these tools. This ensures users understand what they're doing and take responsibility for their usage.

See `examples/` directory for templates and the sections below for usage patterns.

### API Usage - Fetching Campus Data

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

### Web Scraping Usage - Download Project Subjects

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

# Download attachments for a specific project
for project in projects:
    if project['name'] == 'libft':
        attachments = scraper.get_project_attachments(project['url'])
        for url in attachments:
            filename = url.split('/')[-1]
            scraper.download_attachment(url, f'downloads/{filename}')
```

**You must implement:**
- Progress tracking (using `tqdm`)
- Error handling
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
  - `scraper_example.py` - Template for scraping implementation

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
print(f"Found {len(projects)} projects")

# Get attachments for a specific project
attachments = scraper.get_project_attachments('/projects/42cursus-libft')

# Download a file
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
api_login/
├── intra42.py              # Core library (IntraAPI + IntraScrape classes)
├── test_intra42.py         # Test suite
├── scraper_experiment.ipynb # Interactive notebook for HTML exploration
├── examples/
│   └── scraper_example.py  # Template for building your own scraper
├── requirements.txt        # Dependencies
├── .env                    # Configuration (not in git, create from .env.example)
├── .env.example            # Configuration template
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

**Note**: Implementation scripts are intentionally not included in the repository. Users must write their own scripts using the provided library classes. This ensures users understand the code they're running and take responsibility for their usage.

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
       scrape_project(project)
       time.sleep(1)  # 1 second between requests
   ```

2. **Cookie Refresh**: Session cookies expire - check if downloads start failing

3. **Incremental Scraping**: The scraper automatically skips existing files

4. **Error Monitoring**: Check console output for failed projects

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

This tool respects web scraping standards and has been verified against robots.txt:

### Compliance Status

✅ **projects.intra.42.fr/robots.txt** - No active restrictions (all `Disallow` directives are commented out)
✅ **api.intra.42.fr/robots.txt** - No active restrictions, publicly accessible API

### Responsible Usage

While robots.txt permits scraping, this tool implements responsible practices:

- **Authenticated Access**: Uses your personal session cookies (scraping content you have legitimate access to)
- **Rate Limiting**: Built-in delays between requests to avoid overwhelming servers
- **Graceful Interruption**: Proper Ctrl+C handling prevents incomplete/corrupted downloads
- **Smart Resume**: Skips already downloaded files to minimize redundant requests
- **Timeout Handling**: 30-second timeouts prevent hanging connections

### Ethical Considerations

- **Purpose**: Personal archival of educational materials you have access to
- **Scope**: Only downloads project subjects you're authorized to view
- **Impact**: Minimal server load due to rate limiting and smart caching
- **Transparency**: Open source tool with clear documentation

**Note**: robots.txt compliance does not supersede 42's Terms of Service. This tool is intended for personal, educational use by authorized 42 students.

## Contributing

Feel free to submit issues or pull requests!

## Disclaimer

This tool is for educational purposes and personal archival. Respect 42's terms of service and be considerate with your usage (rate limiting, etc.).

## License

MIT License - See LICENSE file for details

## Author

Created by a 42 Berlin student for archiving project subjects.
