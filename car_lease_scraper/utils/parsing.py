"""
Parsing Utilities

Provides utility functions for text parsing and data extraction.
"""

import re
from typing import Optional, Union


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean text by removing excess whitespace and normalizing.
    
    Args:
        text (str, optional): Text to clean
        
    Returns:
        str, optional: Cleaned text
    """
    if not text:
        return None
    
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')
    
    return text


def extract_price(text: Optional[str]) -> float:
    """
    Extract price from text.
    
    Args:
        text (str, optional): Text containing a price
        
    Returns:
        float: Extracted price or 0.0 if extraction fails
    """
    if not text:
        return 0.0
    
    # Extract digits and decimal/thousand separators
    price_match = re.search(r'(\d[\d.,]*)', text)
    if not price_match:
        return 0.0
    
    price_str = price_match.group(1)
    
    # Handle different number formats
    # For Dutch format (€ 123,45)
    if ',' in price_str and '.' not in price_str:
        price_str = price_str.replace(',', '.')
    # For format with thousand separators (€ 1.234,56)
    elif ',' in price_str and '.' in price_str:
        price_str = price_str.replace('.', '').replace(',', '.')
    
    try:
        return round(float(price_str), 2)
    except ValueError:
        return 0.0


def extract_number(text: Optional[str]) -> Optional[int]:
    """
    Extract a number from text.
    
    Args:
        text (str, optional): Text containing a number
        
    Returns:
        int, optional: Extracted number or None if extraction fails
    """
    if not text:
        return None
    
    # Extract digits
    number_match = re.search(r'(\d[\d.,]*)', text)
    if not number_match:
        return None
    
    number_str = number_match.group(1)
    
    # Remove thousand separators
    number_str = number_str.replace('.', '').replace(',', '')
    
    try:
        return int(number_str)
    except ValueError:
        return None


def normalize_make_model(make: str, model: str) -> tuple[str, str]:
    """
    Normalize car make and model.
    
    Args:
        make (str): Car make
        model (str): Car model
        
    Returns:
        tuple[str, str]: Normalized (make, model)
    """
    # Convert to title case
    make = make.title()
    
    # Common abbreviations and specific cases
    make_corrections = {
        "Vw": "Volkswagen",
        "Bmw": "BMW",
        "Mercedes": "Mercedes-Benz",
        "Mercedes Benz": "Mercedes-Benz",
        "Citroen": "Citroën",
    }
    
    # Apply corrections
    return make_corrections.get(make, make), model