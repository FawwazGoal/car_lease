"""
Lease Offer Model

Defines the data model for car lease offers.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator, HttpUrl


class LeaseOffer(BaseModel):
    """
    Model representing a car lease offer.
    
    Attributes:
        car_make (str): Car manufacturer
        car_model (str): Car model name
        version (str, optional): Version or trim level
        monthly_price (float): Monthly lease price
        lease_term_months (int): Duration of the lease in months
        kilometers_per_year (int): Included kilometers per year
        delivery_time (str, optional): Estimated delivery time
        promotional_tags (List[str]): List of promotional tags or special offers
        image_url (HttpUrl, optional): URL to the car image
        scrape_timestamp (datetime): When the data was scraped
        source_url (HttpUrl): URL of the source page
        provider (str): Name of the leasing provider
        raw_data (Dict, optional): Raw data from the scraper
    """
    
    car_make: str
    car_model: str
    version: Optional[str] = None
    monthly_price: float
    lease_term_months: int
    kilometers_per_year: int
    delivery_time: Optional[str] = None
    promotional_tags: List[str] = Field(default_factory=list)
    image_url: Optional[HttpUrl] = None
    scrape_timestamp: datetime = Field(default_factory=datetime.now)
    source_url: HttpUrl
    provider: str
    raw_data: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('monthly_price')
    def validate_price(cls, v):
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @validator('kilometers_per_year')
    def validate_kilometers(cls, v):
        """Validate kilometers per year is within reasonable range."""
        if v <= 0:
            raise ValueError("Kilometers per year must be positive")
        if v > 100000:
            raise ValueError("Kilometers per year seems unreasonably high")
        return v
    
    @validator('lease_term_months')
    def validate_lease_term(cls, v):
        """Validate lease term is within reasonable range."""
        if v <= 0:
            raise ValueError("Lease term must be positive")
        if v > 120:  # 10 years
            raise ValueError("Lease term seems unreasonably long")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        result = self.dict(exclude={'raw_data'})
        result['promotional_tags'] = ','.join(self.promotional_tags)
        result['scrape_timestamp'] = self.scrape_timestamp.isoformat()
        return result