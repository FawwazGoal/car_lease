"""
ANWB Private Lease Scraper - Updated for current website structure

Implements a scraper for ANWB Private Lease website.
"""

import re
from typing import List, Optional, Tuple

from playwright.async_api import Page, ElementHandle

from car_lease_scraper.core.base_scraper import BaseScraper
from car_lease_scraper.models.lease_offer import LeaseOffer
from car_lease_scraper.utils.parsing import clean_text, extract_price


class ANWBPrivateLeaseScraper(BaseScraper):
    """
    Scraper for ANWB Private Lease website.
    
    Extracts car leasing offers including make, model, price, and terms.
    """
    
    provider_name = "anwb"
    base_url = "https://www.anwb.nl/auto/private-lease"
    
    async def extract_offers(self, page: Page) -> List[LeaseOffer]:
        """
        Extract lease offers from ANWB page.
        
        Args:
            page (Page): Playwright page object
            
        Returns:
            List[LeaseOffer]: List of extracted lease offers
        """
        self.logger.info("Starting extraction process")
        
        try:
            # First handle cookie consent if present
            await self._handle_cookie_consent(page)
            
            # Take a screenshot to see where we are
            await page.screenshot(path="after_consent.png")
            
            # Try to find and click on links that might lead to car listings
            await self._navigate_to_car_listings(page)
            
            # Take a screenshot after navigation attempts
            await page.screenshot(path="current_page.png")
            
            # Save current page content for analysis
            html_content = await page.content()
            with open("current_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Try to find car elements with various selectors
            car_elements = await self._find_car_elements(page)
            
            if not car_elements or len(car_elements) == 0:
                self.logger.warning("Could not find any car elements")
                return []
            
            # Process found elements
            offers = []
            for element in car_elements:
                try:
                    offer = await self._extract_offer_data(page, element)
                    if offer:
                        offers.append(offer)
                except Exception as e:
                    self.logger.error(f"Error extracting offer: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(offers)} offers")
            return offers
            
        except Exception as e:
            self.logger.error(f"Error during extraction: {str(e)}")
            await page.screenshot(path="error_screenshot.png")
            return []
    
    async def _handle_cookie_consent(self, page: Page):
        """Handle cookie consent dialogs."""
        self.logger.info("Checking for cookie consent dialogs")
        
        try:
            # Check for typical cookie accept buttons
            consent_selectors = [
                "button:has-text('Accepteren')",
                "button:has-text('Akkoord')",
                "button:has-text('Accept')",
                "button:has-text('Accept all')",
                "button[id*='accept']",
                "button[class*='accept']",
                "button[data-testid*='cookie-accept']"
            ]
            
            for selector in consent_selectors:
                try:
                    visible = await page.is_visible(selector, timeout=2000)
                    if visible:
                        self.logger.info(f"Found consent dialog with selector: {selector}")
                        await page.click(selector)
                        self.logger.info("Clicked consent button")
                        await page.wait_for_load_state("networkidle", timeout=5000)
                        break
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"Error handling cookie consent: {str(e)}")
    
    async def _navigate_to_car_listings(self, page: Page):
        """Try to navigate to car listings page."""
        self.logger.info("Looking for links to car listings")
        
        # Potential links that might lead to car listings
        listing_link_selectors = [
            "a:has-text('Bekijk alle auto's')",   # View all cars
            "a:has-text('Aanbod')",               # Offers
            "a:has-text('Alle auto's')",          # All cars
            "a:has-text('Modellen')",             # Models
            "a:has-text('Private lease')",        # Private lease
            "a:has-text('Lease aanbiedingen')",   # Lease offers
            "a:has-text('Auto zoeken')",          # Search car
            "a:has-text('Aanbod bekijken')",      # View offers
            "a:has-text('Zoeken')",               # Search
            "button:has-text('Auto's bekijken')"  # View cars
        ]
        
        for selector in listing_link_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    self.logger.info(f"Found link to listings with selector: {selector}")
                    
                    # Get the current URL before clicking
                    original_url = page.url
                    
                    # Click the link
                    await page.click(selector)
                    self.logger.info(f"Clicked on: {selector}")
                    
                    # Wait for navigation
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Check if URL changed
                    new_url = page.url
                    if new_url != original_url:
                        self.logger.info(f"Navigation successful. New URL: {new_url}")
                        return
                    else:
                        self.logger.info("URL did not change after clicking")
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
        
        self.logger.warning("Could not navigate to car listings page through links")
    
    async def _find_car_elements(self, page: Page) -> List[ElementHandle]:
        """Find car elements on the page."""
        self.logger.info("Looking for car elements")
        
        # Try standard selectors first
        car_selectors = [
            ".car-card", ".card-car", ".car-tile", 
            ".lease-car", ".lease-tile", ".car-item",
            ".product-item", "article.card", ".auto-card",
            "div[class*='car']", "div[class*='auto']", 
            "div[class*='lease']", ".card"
        ]
        
        for selector in car_selectors:
            try:
                self.logger.info(f"Trying selector: {selector}")
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    return elements
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
        
        # If standard selectors fail, try looking for elements with car-related content
        self.logger.info("Using content-based detection for car elements")
        elements = await self._find_car_elements_by_content(page)
        
        return elements
    
    async def _find_car_elements_by_content(self, page: Page) -> List[ElementHandle]:
        """Find car elements by looking for typical car content."""
        self.logger.info("Looking for elements with car-related content")
        
        # Try to find any elements that might be card-like containers
        container_selectors = [
            "div.card", "article", ".item", 
            "div.product", "div.grid > div", 
            "div.row > div", "div.flex > div"
        ]
        
        all_potential_elements = []
        
        for selector in container_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    self.logger.info(f"Found {len(elements)} potential container elements with selector: {selector}")
                    all_potential_elements.extend(elements)
            except Exception:
                continue
        
        # Filter elements to those that seem to contain car information
        car_elements = []
        for element in all_potential_elements:
            try:
                text_content = await element.text_content()
                
                # Check if the element contains typical car-related text
                if re.search(r'(?:Volkswagen|Toyota|BMW|Audi|Mercedes|Opel|Renault|Ford|Kia)', text_content, re.IGNORECASE) and \
                   re.search(r'(?:€|euro)', text_content, re.IGNORECASE) and \
                   re.search(r'(?:p/m|per maand|lease)', text_content, re.IGNORECASE):
                    car_elements.append(element)
            except Exception:
                continue
        
        self.logger.info(f"Found {len(car_elements)} elements with car-related content")
        return car_elements
    
    async def _extract_offer_data(self, page: Page, offer_element: ElementHandle) -> Optional[LeaseOffer]:
        """
        Extract data from an individual offer element.
        
        Args:
            page (Page): Playwright page object
            offer_element (ElementHandle): Element containing the offer
            
        Returns:
            Optional[LeaseOffer]: Extracted lease offer or None if extraction failed
        """
        try:
            # Take a screenshot of this element for debugging
            element_html = await page.evaluate("(el) => el.outerHTML", offer_element)
            with open("car_element.html", "w", encoding="utf-8") as f:
                f.write(element_html)
            
            # Look for car make/model
            title_selectors = [
                "h2", "h3", "h4", 
                "[class*='title']", "[class*='name']", "[class*='model']",
                "div[class*='car-']", "span[class*='car-']"
            ]
            
            car_title = None
            car_title_text = ""
            
            for selector in title_selectors:
                title_element = await offer_element.query_selector(selector)
                if title_element:
                    title_text = await title_element.text_content()
                    title_text = clean_text(title_text)
                    if title_text and len(title_text) > 3:
                        car_title = title_element
                        car_title_text = title_text
                        self.logger.info(f"Found car title: {car_title_text}")
                        break
            
            if not car_title:
                # If no title element found, try to extract it from the full text
                full_text = await offer_element.text_content()
                car_title_text = self._extract_car_title_from_text(full_text)
                if not car_title_text:
                    self.logger.warning("Could not find car title")
                    return None
            
            car_make, car_model = self._parse_car_make_model(car_title_text)
            
            # Look for price
            price = 0.0
            price_selectors = [
                "span:has-text('€')", "[class*='price']", "[class*='amount']",
                "div:has-text('€')", "span[class*='cost']"
            ]
            
            for selector in price_selectors:
                price_element = await offer_element.query_selector(selector)
                if price_element:
                    price_text = await price_element.text_content()
                    price = extract_price(price_text)
                    if price > 0:
                        self.logger.info(f"Found price: €{price:.2f}")
                        break
            
            if price <= 0:
                self.logger.warning("Could not find valid price")
                return None
            
            # Extract other details with more flexible approach
            details_text = await offer_element.text_content()
            
            # Extract lease terms
            lease_term = 48  # Default
            kilometers = 10000  # Default
            
            # Look for month/kilometers pattern in the text
            term_match = re.search(r'(\d+)\s*(?:maanden|mnd)', details_text, re.IGNORECASE)
            if term_match:
                lease_term = int(term_match.group(1))
            
            km_match = re.search(r'(\d[\d.,]*)\s*(?:km|kilometer)', details_text, re.IGNORECASE)
            if km_match:
                km_text = km_match.group(1).replace('.', '').replace(',', '')
                kilometers = int(km_text)
            
            # Extract version/trim
            version = self._extract_version(details_text, car_make, car_model)
            
            # Extract delivery time if available
            delivery_time = None
            delivery_patterns = [
                r'levertijd\s*:\s*([^\.]+)',
                r'levertijd\s*([^\.]+)',
                r'levertermijn\s*:\s*([^\.]+)',
                r'binnen\s*(\d+\s*(?:dagen|weken|maanden))'
            ]
            
            for pattern in delivery_patterns:
                delivery_match = re.search(pattern, details_text, re.IGNORECASE)
                if delivery_match:
                    delivery_time = clean_text(delivery_match.group(1))
                    break
            
            # Extract promotional tags
            promo_tags = []
            promo_patterns = [
                r'nu met voordeel',
                r'actie',
                r'aanbieding',
                r'special',
                r'bonus',
                r'korting',
                r'gratis'
            ]
            
            for pattern in promo_patterns:
                if re.search(pattern, details_text, re.IGNORECASE):
                    promo_tags.append(pattern.capitalize())
            
            # Extract image URL
            image_url = None
            image_element = await offer_element.query_selector("img")
            if image_element:
                image_url = await image_element.get_attribute("src")
            
            # Create LeaseOffer object
            offer = LeaseOffer(
                car_make=car_make,
                car_model=car_model,
                version=version,
                monthly_price=price,
                lease_term_months=lease_term,
                kilometers_per_year=kilometers,
                delivery_time=delivery_time,
                promotional_tags=promo_tags,
                image_url=image_url,
                source_url=self.car_listings_url,
                provider=self.provider_name,
                raw_data={
                    "title": car_title_text,
                    "details": details_text
                }
            )
            
            return offer
        
        except Exception as e:
            self.logger.error(f"Error extracting offer data: {str(e)}")
            return None
    
    def _extract_car_title_from_text(self, text: str) -> str:
        """Extract car title from full text."""
        # Look for common car brand patterns
        common_brands = [
            "Volkswagen", "Opel", "Peugeot", "Toyota", "Renault", 
            "Ford", "Kia", "Audi", "BMW", "Citroën", "Seat", "Skoda", 
            "Hyundai", "Mercedes", "Volvo", "Mazda", "Nissan", "Suzuki", 
            "Fiat", "Mitsubishi", "Honda", "Dacia", "Porsche", "Tesla"
        ]
        
        for brand in common_brands:
            pattern = fr'{brand}\s+([A-Za-z0-9\s\-]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
                return f"{brand} {model}"
        
        return ""
    
    def _parse_car_make_model(self, car_title: str) -> Tuple[str, str]:
        """
        Parse car make and model from the title.
        
        Args:
            car_title (str): Car title text
            
        Returns:
            Tuple[str, str]: (make, model)
        """
        if not car_title:
            return "Unknown", "Unknown"
        
        # Common Dutch car brands to check first
        common_brands = [
            "Volkswagen", "Opel", "Peugeot", "Toyota", "Renault", 
            "Ford", "Kia", "Audi", "BMW", "Citroën", "Seat", "Skoda", 
            "Hyundai", "Mercedes", "Volvo", "Mazda", "Nissan", "Suzuki", 
            "Fiat", "Mitsubishi", "Honda", "Dacia", "Porsche", "Tesla"
        ]
        
        for brand in common_brands:
            if car_title.lower().startswith(brand.lower()):
                return brand, car_title[len(brand):].strip()
        
        # Default fallback: split on first space
        parts = car_title.split(" ", 1)
        if len(parts) == 1:
            return parts[0], "Unknown"
        return parts[0], parts[1]
    
    def _extract_version(self, details_text: str, make: str, model: str) -> Optional[str]:
        """Extract version/trim from details text."""
        # Remove car make and model from the text to avoid confusion
        cleaned_text = details_text.replace(make, "").replace(model, "")
        
        # Look for common version/trim patterns
        patterns = [
            r'(\d\.\d+\s*[A-Za-z]*)',  # Engine size (e.g., 1.6 TDI)
            r'([A-Za-z]+\s*(?:line|edition|series))',  # Line/Edition (e.g., Comfort Line)
            r'((?:comfort|business|sport|luxury)\s*(?:line|edition|pack))',  # Common trim names
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def has_next_page(self, page: Page) -> bool:
        """
        Check if there's a next page.
        
        Args:
            page (Page): Playwright page object
            
        Returns:
            bool: Whether there is a next page
        """
        pagination_selectors = [
            "a.pagination-next", 
            "a[aria-label='Next page']",
            "button[aria-label='Next page']",
            "a.next-page",
            "button.next-page",
            "a:has-text('Volgende')",  # Dutch for "Next"
            "button:has-text('Volgende')"
        ]
        
        for selector in pagination_selectors:
            try:
                next_button = await page.query_selector(selector + ":not([disabled])")
                if next_button:
                    return True
            except Exception:
                continue
        
        return False
    
    async def go_to_next_page(self, page: Page):
        """
        Navigate to the next page.
        
        Args:
            page (Page): Playwright page object
        """
        pagination_selectors = [
            "a.pagination-next", 
            "a[aria-label='Next page']",
            "button[aria-label='Next page']",
            "a.next-page",
            "button.next-page",
            "a:has-text('Volgende')",  # Dutch for "Next"
            "button:has-text('Volgende')"
        ]
        
        for selector in pagination_selectors:
            try:
                next_button = await page.query_selector(selector + ":not([disabled])")
                if next_button:
                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path=f"page_{page.url}.png")
                    return
            except Exception:
                continue
        
        self.logger.warning("Could not navigate to next page")