"""
Configuration Module

Handles configuration settings for the car lease scraper.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Update the import to use pydantic-settings
from pydantic_settings import BaseSettings
from pydantic import HttpUrl, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        headless (bool): Whether to run browser in headless mode
        default_user_agent (str): Default user agent string
        output_dir (Path): Directory for output files
        default_format (str): Default output format (json or csv)
        max_retries (int): Maximum number of retries for failed requests
        request_delay (float): Delay between requests in seconds
        max_pages (int): Maximum number of pages to scrape per provider
        page_load_timeout (int): Timeout for page loading in milliseconds
        log_level (str): Logging level
    """
    
    # Browser settings
    headless: bool = True
    default_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    
    # Output settings
    output_dir: Path = Path("./data")
    default_format: str = "json"
    
    # Scraping behavior
    max_retries: int = 3
    request_delay: float = 2.0
    max_pages: int = 5
    page_load_timeout: int = 30000
    
    # Logging
    log_level: str = "INFO"
    
    @validator("output_dir")
    def create_output_dir(cls, v):
        """Ensure output directory exists."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @validator("default_format")
    def validate_format(cls, v):
        """Validate output format."""
        if v.lower() not in ["json", "csv"]:
            raise ValueError(f"Invalid format: {v}. Must be either 'json' or 'csv'")
        return v.lower()
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
SETTINGS = Settings()