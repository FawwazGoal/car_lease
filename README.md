# Car Lease Scraper

A modular web scraping solution for collecting car leasing offers from Dutch leasing providers.

## Features

- Scrapes car leasing offers from major Dutch leasing providers
- Extracts key data: car make & model, version, price, lease terms, etc.
- Modular architecture allows easy extension to new providers
- Robust handling of anti-scraping measures
- Data validation and transformation pipeline
- Multiple output formats (JSON, CSV)

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [As a Library](#as-a-library)
  - [Docker](#docker)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Adding a New Provider](#adding-a-new-provider)
- [Testing](#testing)
- [Assumptions and Limitations](#assumptions-and-limitations)

## Installation

### Option 1: Standard Python Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/car-lease-scraper.git
cd car-lease-scraper

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install the package in development mode
pip install -e .
```

### Option 2: Docker Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/car-lease-scraper.git
cd car-lease-scraper

# Build the Docker image
docker build -t car-lease-scraper .
```

## Usage

### Command Line

```bash
# Scrape ANWB Private Lease
python -m car_lease_scraper --provider anwb

# Save output to specific format
python -m car_lease_scraper --provider anwb --output-format json,csv

# Specify output directory
python -m car_lease_scraper --provider anwb --output-dir ./data

# List available providers
python -m car_lease_scraper --list
```

### As a Library

```python
import asyncio
from car_lease_scraper.scrapers import ANWBPrivateLeaseScraper
from car_lease_scraper.pipeline import DataProcessor

async def scrape_anwb():
    scraper = ANWBPrivateLeaseScraper()
    processor = DataProcessor()
    
    raw_data = await scraper.scrape()
    processed_data = processor.process(raw_data)
    
    # Save to JSON
    processed_data.save_to_json("anwb_offers.json")
    
    # Save to CSV
    processed_data.save_to_csv("anwb_offers.csv")

# Run the scraper
asyncio.run(scrape_anwb())
```

### Docker

#### Using Docker Run

```bash
# Create a directory for output data
mkdir -p data

# Run the scraper with Docker
docker run --rm -v "$(pwd)/data:/app/data" car-lease-scraper --provider anwb
```

#### Using Docker Compose

```bash
# Run with default settings (ANWB provider)
docker-compose up scraper

# Run with different provider
docker-compose run --rm scraper --provider other_provider

# Run tests
docker-compose run --rm test
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
car_lease_scraper/
│
├── core/                 # Core functionality
│   ├── base_scraper.py   # Abstract base scraper class
│   ├── browser.py        # Browser management
│   ├── validation.py     # Data validation utilities
│   └── storage.py        # Data storage utilities
│
├── models/               # Data models
│   └── lease_offer.py    # LeaseOffer data model
│
├── scrapers/             # Specific website scrapers
│   ├── anwb_scraper.py   # ANWB specific scraper
│   └── registry.py       # Scraper registry for discovery
│
├── pipeline/             # Data processing pipeline
│   ├── processor.py      # Data processing pipeline
│   ├── extractors.py     # Data extraction components
│   ├── transformers.py   # Data transformation components
│   └── loaders.py        # Data loading components
│
└── utils/                # Utility functions
    ├── logging.py        # Logging setup and utilities
    ├── parsing.py        # Parsing helpers
    └── anti_bot.py       # Anti-bot detection and evasion
```

## Configuration

Configuration is handled through environment variables or a `.env` file:

```
# Browser settings
HEADLESS=true
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36

# Output settings
OUTPUT_DIR=./data
DEFAULT_FORMAT=json

# Scraping behavior
MAX_RETRIES=3
REQUEST_DELAY=2
MAX_PAGES=5
LOG_LEVEL=INFO
```

## Adding a New Provider

To add support for a new leasing provider:

1. Create a new scraper in `car_lease_scraper/scrapers/`
2. Extend the `BaseScraper` class
3. Implement the required methods
4. Register the scraper in `car_lease_scraper/scrapers/registry.py`

Example:

```python
from car_lease_scraper.core.base_scraper import BaseScraper

class NewProviderScraper(BaseScraper):
    """Scraper for New Provider website"""
    
    provider_name = "new_provider"
    base_url = "https://www.newprovider.nl/lease-aanbiedingen"
    
    async def extract_offers(self, page):
        # Implementation details
        pass
```

## Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=car_lease_scraper

# Run tests for a specific module
pytest tests/test_anwb_scraper.py
```

Using Docker:

```bash
# Run all tests with Docker
docker-compose run --rm test
```

## Assumptions and Limitations

- **Website Structure**: The implementation assumes the current HTML structure of the ANWB website. If the layout changes significantly, selectors may need to be updated.

- **Anti-Bot Measures**: This scraper implements basic anti-bot evasion techniques, but sophisticated detection systems may still block it. For production use, consider additional measures like proxy rotation.

- **JavaScript Rendering**: The scraped websites require JavaScript for full content rendering, which is why we use Playwright instead of simpler HTTP-based scrapers.

- **Rate Limiting**: The scraper implements polite scraping with delays to respect website resources. Adjust the request delay based on the target website's capabilities.

- **Scalability**: The current implementation runs sequentially. For scraping multiple providers in parallel, additional orchestration would be needed.

- **Error Handling**: While basic error handling is implemented, production use would benefit from more sophisticated recovery strategies and alerting mechanisms.

## License

This project is licensed under the MIT License - see the LICENSE file for details.