"""
Anti-Bot Utilities

Provides utilities to help evade bot detection while scraping.
"""

import asyncio
import random
from typing import Optional, List

from playwright.async_api import BrowserContext, Page

from car_lease_scraper.utils.logging import get_logger


logger = get_logger("anti_bot")


async def add_stealth_scripts(context: BrowserContext):
    """
    Add scripts to the browser context to evade bot detection.
    
    Args:
        context (BrowserContext): Playwright browser context
    """
    # Hide webdriver property
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    """)
    
    # Add canvas noise to prevent fingerprinting
    await context.add_init_script("""
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            const context = originalGetContext.apply(this, arguments);
            if (type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function() {
                    const args = arguments;
                    args[0] = args[0] + ' '; // Add tiny noise
                    return originalFillText.apply(this, args);
                };
            }
            return context;
        };
    """)
    
    # Mask plugins and mime types
    await context.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        name: "PDF Viewer",
                        filename: "internal-pdf-viewer",
                        description: "Portable Document Format",
                        length: 1
                    }
                ];
            },
        });
    """)


async def detect_captcha(page: Page) -> bool:
    """
    Detect if a page contains a CAPTCHA challenge.
    
    Args:
        page (Page): Playwright page object
        
    Returns:
        bool: Whether a CAPTCHA was detected
    """
    captcha_indicators = [
        # Text indicators
        "captcha", "robot", "human verification", "security check", "prove you're human",
        # Common CAPTCHA providers
        "recaptcha", "hcaptcha", "arkoselabs", "funcaptcha", "turnstile",
        # Common CAPTCHA element IDs and classes
        "#captcha", ".captcha", "#recaptcha", ".g-recaptcha", ".h-captcha"
    ]
    
    # Check page content for CAPTCHA indicators
    content = await page.content()
    content_lower = content.lower()
    
    for indicator in captcha_indicators:
        if indicator in content_lower:
            logger.warning(f"CAPTCHA detected: {indicator}")
            return True
    
    # Check for CAPTCHA elements
    for indicator in captcha_indicators:
        if indicator.startswith('#') or indicator.startswith('.'):
            element = await page.query_selector(indicator)
            if element:
                logger.warning(f"CAPTCHA element detected: {indicator}")
                return True
    
    return False


async def handle_captcha(page: Page) -> bool:
    """
    Attempt to handle a detected CAPTCHA.
    
    Args:
        page (Page): Playwright page object
        
    Returns:
        bool: Whether the CAPTCHA was successfully handled
    """
    # In a real implementation, you might:
    # 1. Integrate with a CAPTCHA solving service
    # 2. Implement specific handling for known CAPTCHA types
    # 3. Notify a human operator for assistance
    
    # For this example, we'll just log and wait
    logger.warning("CAPTCHA handling not implemented. Waiting to see if it times out...")
    await asyncio.sleep(5)
    
    # Check if CAPTCHA is still present
    still_present = await detect_captcha(page)
    if still_present:
        logger.error("CAPTCHA still present after waiting")
        return False
    
    logger.info("CAPTCHA appears to be gone, continuing")
    return True


async def simulate_human_behavior(page: Page):
    """
    Simulate human-like behavior to avoid bot detection.
    
    Args:
        page (Page): Playwright page object
    """
    # Random delay before any actions
    await asyncio.sleep(random.uniform(1, 3))
    
    # Get page dimensions
    viewport = await page.evaluate("""
        () => ({
            width: window.innerWidth,
            height: window.innerHeight
        })
    """)
    
    # Perform random mouse movements
    for _ in range(random.randint(3, 8)):
        await page.mouse.move(
            random.randint(100, viewport['width'] - 200),
            random.randint(100, viewport['height'] - 200),
            steps=random.randint(5, 15)  # Move in steps for more human-like movement
        )
        await asyncio.sleep(random.uniform(0.1, 0.5))
    
    # Random scrolling
    scroll_amount = random.randint(300, 1000)
    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # Scroll back up a bit
    await page.evaluate(f"window.scrollBy(0, {-scroll_amount // 2})")
    await asyncio.sleep(random.uniform(0.3, 0.7))