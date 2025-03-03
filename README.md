# AI Daily Digest

RSS feed aggregator for AI-related news and updates. This project scrapes content from various AI blogs and news sources, generating standardized feeds that can be consumed by any RSS reader.

## Features

- Scrapes content from multiple AI-related sources
- Generates RSS, Atom, and JSON feeds
- Categorizes content by source type (AI companies, tools, news, etc.)
- Filters content to ensure it's AI-related
- Automatically runs via GitHub Actions
- Publishes feeds to GitHub Pages

## Setup

### Using Poetry (recommended)

1. Clone this repository
2. Install Poetry (if not already installed):
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Install dependencies:
   ```
   poetry install
   ```
4. Run the scraper:
   ```
   poetry run python -m src.main
   ```

### Alternative: Using pip

1. Clone this repository
2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   Note: The requirements.txt file can be generated from Poetry with:
   ```
   poetry export -f requirements.txt --output requirements.txt
   ```

## Usage

Run the scraper manually:

```
# With Poetry
poetry run python -m src.main

# Without Poetry
python -m src.main
```

Options:
- `--output-dir`: Directory to save the generated feeds (default: `./feeds`)
- `--ai-only`: Enable filtering to only include AI-related content

## GitHub Actions Setup

This project is designed to be run automatically via GitHub Actions. The workflow will:

1. Check out the repository
2. Set up Python and Poetry
3. Install dependencies
4. Run the scraper
5. Push the generated feeds to the `gh-pages` branch

GitHub Actions will run on a schedule (every 6 hours by default) and also can be triggered manually.

## Customizing Feeds

Edit the `src/config.py` file to:
- Add or remove RSS feed sources
- Modify the AI keywords used for filtering
- Change output directories

## Development

### Project Structure

```
.
├── .github/workflows/ - GitHub Actions workflows
├── feeds/             - Generated feed files
├── src/               - Source code
│   ├── __init__.py    - Package initialization
│   ├── main.py        - Main entry point
│   ├── config.py      - Configuration settings
│   └── scrapers/      - Scraper implementations
│       ├── __init__.py
│       ├── base_scraper.py - Base scraper class
│       └── rss_scraper.py  - RSS scraper implementation
├── pyproject.toml     - Poetry configuration
└── README.md          - Documentation
```

### Adding a New Source

To add a new source:

1. Open `src/config.py`
2. Add your source to the `FEEDS` dictionary:
```python
'Source Name': {
    'url': 'https://example.com/feed.xml',
    'category': 'category_name',
},
```

## License

MIT