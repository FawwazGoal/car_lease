"""
Test Configuration

Shared fixtures and utilities for tests.
"""

import os
import pytest
import asyncio
from pathlib import Path
from typing import Generator

from car_lease_scraper.config import SETTINGS


@pytest.fixture
def test_output_dir() -> Generator[Path, None, None]:
    """
    Create a temporary test output directory.
    
    Yields:
        Path: Path to temporary output directory
    """
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)
    
    yield test_dir
    
    # Cleanup after tests
    # Note: In a real implementation, you might want to remove files
    # but for testing purposes, we'll keep them for inspection
    pass


@pytest.fixture
def sample_lease_offer_data() -> dict:
    """
    Sample lease offer data for testing.
    
    Returns:
        dict: Sample lease offer data
    """
    return {
        "car_make": "Volkswagen",
        "car_model": "Golf",
        "version": "Comfort Line 1.5 TSI",
        "monthly_price": 389.0,
        "lease_term_months": 48,
        "kilometers_per_year": 10000,
        "delivery_time": "Levertijd: 2-3 maanden",
        "promotional_tags": ["Nu met voordeel", "Actie"],
        "image_url": "https://example.com/car.jpg",
        "source_url": "https://www.anwb.nl/auto/private-lease",
        "provider": "anwb"
    }


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async tests.
    
    This is needed for pytest-asyncio to work with session-scoped fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """
    Set up test environment variables.
    
    This fixture runs automatically for all tests.
    """
    monkeypatch.setenv("HEADLESS", "true")
    monkeypatch.setenv("OUTPUT_DIR", "./test_output")
    monkeypatch.setenv("MAX_RETRIES", "1")
    monkeypatch.setenv("MAX_PAGES", "1")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Reduce log noise during tests