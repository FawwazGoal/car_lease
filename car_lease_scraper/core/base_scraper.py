"""
Base Scraper Module

Provides an abstract base class for implementing specific website scrapers.
All provider-specific scrapers should extend this class.
"""

import abc
import asyncio
import logging
from typing import List, Optional, Dict, Any

from playwright.async_api import Page, TimeoutError

from car_lease_scraper.core.browser import BrowserManager
from car_lease_scraper.models.lease_offer import LeaseOffer
from car_lease_scraper.utils.logging import get_logger


class BaseScraper(abc.ABC):
    """
    Abstract base scraper class that defines the interface for all specific scrapers.
    
    Attributes:
        provider_name (str): Name of the leasing provider
        base_url (str): Base URL for the provider's website
        logger (logging.Logger): Logger instance
    """
    
    provider_name: str = None
    base_url: str = None
    
    def __init__(self, headless: bool = True, max_pages: int = 5):
        """
        Initialize the base scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            max_pages (int): Maximum number of pages to scrape
        """
        if not self.provider_name or not self.base_url:
            raise ValueError("provider_name and base_url must be defined in subclasses")
        
        self.headless = headless
        self.max_pages = max_pages
        self.logger = get_logger(f"{self.provider_name}_scraper")
        self.browser_manager = BrowserManager(headless=headless)
    
    async def setup(self):
        """Set up resources needed for scraping."""
        await self.browser_manager.setup()
    
    async def teardown(self):
        """Clean up resources after scraping."""
        await self.browser_manager.teardown()
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.teardown()
    
    @abc.abstractmethod
    async def extract_offers(self, page: Page) -> List[LeaseOffer]:
        """
        Extract lease offers from a page.
        
        Args:
            page (Page): Playwright page object
            
        Returns:
            List[LeaseOffer]: List of extracted lease offers
        """
        pass
    
    async def navigate_to_page(self, url: str) -> Page:
        """
        Navigate to a specific URL.
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            Page: Playwright page object
        """
        return await self.browser_manager.navigate_to_page(url)
    
    async def scrape(self) -> List[LeaseOffer]:
        """
        Main method to scrape lease offers.
        
        Returns:
            List[LeaseOffer]: List of all extracted lease offers
        """
        self.logger.info(f"Starting to scrape {self.provider_name} at {self.base_url}")
        
        page = await self.navigate_to_page(self.base_url)
        all_offers = []
        
        try:
            # Extract offers from the first page
            offers = await self.extract_offers(page)
            all_offers.extend(offers)
            self.logger.info(f"Extracted {len(offers)} offers from page 1")
            
            # Handle pagination if implemented by the subclass
            page_num = 1
            while page_num < self.max_pages and await self.has_next_page(page):
                page_num += 1
                self.logger.info(f"Navigating to page {page_num}")
                
                await self.go_to_next_page(page)
                
                offers = await self.extract_offers(page)
                all_offers.extend(offers)
                self.logger.info(f"Extracted {len(offers)} offers from page {page_num}")
            
            self.logger.info(f"Completed scraping {self.provider_name}. Total offers: {len(all_offers)}")
            return all_offers
            
        finally:
            await page.close()
    
    async def has_next_page(self, page: Page) -> bool:
        """
        Check if there is a next page of results.
        
        Args:
            page (Page): Playwright page object
            
        Returns:
            bool: Whether there is a next page
        """
        # Default implementation (no pagination)
        return False
    
    async def go_to_next_page(self, page: Page):
        """
        Navigate to the next page of results.
        
        Args:
            page (Page): Playwright page object
        """
        # Default implementation (no pagination)
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the provider.
        
        Returns:
            Dict[str, Any]: Provider information
        """
        return {
            "name": self.provider_name,
            "url": self.base_url
        }