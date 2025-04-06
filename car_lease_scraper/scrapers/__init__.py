# car_lease_scraper/scrapers/__init__.py
"""
Website-specific scrapers.

Provides implementations for specific leasing providers.
"""

from car_lease_scraper.scrapers.anwb_scraper import ANWBPrivateLeaseScraper
from car_lease_scraper.scrapers.registry import registry

# Register the ANWB scraper explicitly
registry.register(ANWBPrivateLeaseScraper)

__all__ = ["ANWBPrivateLeaseScraper", "registry"]