"""
ANWB Scraper Tests

Tests for the ANWB Private Lease scraper.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from car_lease_scraper.scrapers.anwb_scraper import ANWBPrivateLeaseScraper
from car_lease_scraper.models.lease_offer import LeaseOffer


@pytest.fixture
def mock_offer_element():
    """Create a mock offer element."""
    element = AsyncMock()
    
    # Set up text content returns
    async def mock_text_content():
        return "Volkswagen Golf"
    
    # Mock query_selector to return child elements
    async def mock_query_selector(selector):
        child = AsyncMock()
        
        if selector == ".car-title":
            child.text_content = mock_text_content
            return child
        elif selector == ".car-subtitle":
            child.text_content = AsyncMock(return_value="Comfort Line 1.5 TSI")
            return child
        elif selector == ".price-amount":
            child.text_content = AsyncMock(return_value="€389,00")
            return child
        elif selector == ".lease-terms":
            child.text_content = AsyncMock(return_value="48 maanden, 10.000 km per jaar")
            return child
        elif selector == ".delivery-time":
            child.text_content = AsyncMock(return_value="Levertijd: 2-3 maanden")
            return child
        elif selector == "img.car-image":
            child.get_attribute = AsyncMock(return_value="https://example.com/car.jpg")
            return child
        
        return None
    
    element.query_selector = mock_query_selector
    
    # Mock query_selector_all for promotional tags
    async def mock_query_selector_all(selector):
        if selector == ".promo-tag":
            tag1 = AsyncMock()
            tag1.text_content = AsyncMock(return_value="Nu met voordeel")
            tag2 = AsyncMock()
            tag2.text_content = AsyncMock(return_value="Actie")
            return [tag1, tag2]
        return []
    
    element.query_selector_all = mock_query_selector_all
    
    return element


@pytest.mark.asyncio
async def test_extract_offer_data(mock_offer_element):
    """Test extracting offer data from an element."""
    # Initialize scraper
    scraper = ANWBPrivateLeaseScraper()
    
    # Mock page
    mock_page = AsyncMock()
    
    # Extract offer data
    offer = await scraper._extract_offer_data(mock_page, mock_offer_element)
    
    # Assertions
    assert offer is not None
    assert isinstance(offer, LeaseOffer)
    assert offer.car_make == "Volkswagen"
    assert offer.car_model == "Golf"
    assert offer.version == "Comfort Line 1.5 TSI"
    assert offer.monthly_price == 389.0
    assert offer.lease_term_months == 48
    assert offer.kilometers_per_year == 10000
    assert offer.delivery_time == "Levertijd: 2-3 maanden"
    assert len(offer.promotional_tags) == 2
    assert "Nu met voordeel" in offer.promotional_tags
    assert offer.image_url == "https://example.com/car.jpg"
    assert offer.provider == "anwb"


@pytest.mark.asyncio
async def test_parse_car_make_model():
    """Test parsing car make and model from title."""
    scraper = ANWBPrivateLeaseScraper()
    
    # Test cases
    test_cases = [
        ("Volkswagen Golf", "Volkswagen", "Golf"),
        ("BMW 3 Serie", "BMW", "3 Serie"),
        ("Audi A4 Avant", "Audi", "A4 Avant"),
        ("Tesla Model 3", "Tesla", "Model 3"),
        ("Mercedes-Benz A-Klasse", "Mercedes-Benz", "A-Klasse"),
        ("SingleWord", "SingleWord", "Unknown"),
        ("", "Unknown", "Unknown")
    ]
    
    for input_title, expected_make, expected_model in test_cases:
        make, model = scraper._parse_car_make_model(input_title)
        assert make == expected_make
        assert model == expected_model


@pytest.mark.asyncio
async def test_extract_lease_terms():
    """Test extracting lease terms from element."""
    scraper = ANWBPrivateLeaseScraper()
    
    # Test with valid element
    element = AsyncMock()
    element.text_content = AsyncMock(return_value="60 maanden, 15.000 km per jaar")
    
    months, kilometers = await scraper._extract_lease_terms(element)
    assert months == 60
    assert kilometers == 15000
    
    # Test with different format
    element.text_content = AsyncMock(return_value="36 maanden, 20.000 km")
    months, kilometers = await scraper._extract_lease_terms(element)
    assert months == 36
    assert kilometers == 20000
    
    # Test with None element (should return defaults)
    months, kilometers = await scraper._extract_lease_terms(None)
    assert months == 48
    assert kilometers == 10000


@pytest.mark.asyncio
async def test_has_next_page():
    """Test checking for next page."""
    scraper = ANWBPrivateLeaseScraper()
    
    # Mock page
    page = AsyncMock()
    
    # Test with next page available
    page.query_selector.return_value = AsyncMock()  # Non-None return
    has_next = await scraper.has_next_page(page)
    assert has_next is True
    
    # Test with no next page
    page.query_selector.return_value = None
    has_next = await scraper.has_next_page(page)
    assert has_next is False