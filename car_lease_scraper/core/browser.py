"""
Browser Management Module

Provides a browser manager class for handling browser instances and page navigation.
"""

import asyncio
import random
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from car_lease_scraper.utils.logging import get_logger
from car_lease_scraper.utils.anti_bot import add_stealth_scripts
from car_lease_scraper.config import SETTINGS


class BrowserManager:
    """
    Manages browser instances and provides navigation utilities.
    
    Attributes:
        headless (bool): Whether to run browser in headless mode
        user_agent (str): User agent string to use
        viewport (dict): Viewport dimensions
        logger (logging.Logger): Logger instance
    """
    
    def __init__(
        self, 
        headless: bool = True, 
        user_agent: Optional[str] = None,
        viewport: Optional[dict] = None
    ):
        """
        Initialize the browser manager.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            user_agent (str, optional): User agent string to use
            viewport (dict, optional): Viewport dimensions
        """
        self.headless = headless
        self.user_agent = user_agent or SETTINGS.default_user_agent
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.logger = get_logger("browser")
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def setup(self):
        """Set up browser and context."""
        self.logger.info("Setting up browser")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport=self.viewport,
        )
        
        # Add stealth scripts to evade bot detection
        await add_stealth_scripts(self.context)
    
    async def teardown(self):
        """Clean up browser resources."""
        self.logger.info("Cleaning up browser resources")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()  # Use this instead of __aexit__
    
    @retry(
        stop=stop_after_attempt(SETTINGS.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TimeoutError)
    )
    async def navigate_to_page(self, url: str) -> Page:
        """
        Navigate to a URL with retry logic.
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            Page: Playwright page object
        """
        self.logger.info(f"Navigating to {url}")
        page = await self.context.new_page()
        
        try:
            response = await page.goto(
                url, 
                wait_until="networkidle", 
                timeout=SETTINGS.page_load_timeout
            )
            
            if not response or response.status >= 400:
                self.logger.error(f"Failed to load page: {response.status if response else 'No response'}")
                raise TimeoutError(f"Failed to load page: {url}")
            
            # Add random delay to mimic human behavior
            await asyncio.sleep(random.uniform(1, 3))
            
            # Perform random scrolling
            await self._random_scroll(page)
            
            return page
        except Exception as e:
            await page.close()
            raise e
    
    async def _random_scroll(self, page: Page):
        """
        Perform random scrolling to mimic human behavior.
        
        Args:
            page (Page): Playwright page object
        """
        # Get page height
        page_height = await page.evaluate("document.body.scrollHeight")
        
        # Scroll in chunks with small pauses
        scroll_chunks = min(5, max(2, page_height // 1000))
        chunk_size = page_height / scroll_chunks
        
        for i in range(1, scroll_chunks + 1):
            await page.evaluate(f"window.scrollTo(0, {i * chunk_size})")
            await asyncio.sleep(0.5 + (0.5 * (i / scroll_chunks)))  # Gradually slow down scrolling