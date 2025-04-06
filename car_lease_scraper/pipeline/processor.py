"""
Data Processor Module

Handles the processing pipeline for scraped data.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import pandas as pd

from car_lease_scraper.models.lease_offer import LeaseOffer
from car_lease_scraper.utils.logging import get_logger
from car_lease_scraper.config import SETTINGS


logger = get_logger("data_processor")


class DataProcessor:
    """
    Processes and transforms scraped lease offer data.
    
    Attributes:
        output_dir (Path): Directory for output files
    """
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the processor.
        
        Args:
            output_dir (str or Path, optional): Directory for output files
        """
        self.output_dir = Path(output_dir) if output_dir else SETTINGS.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process(self, offers: List[LeaseOffer]) -> 'ProcessedData':
        """
        Process a list of lease offers.
        
        Args:
            offers (List[LeaseOffer]): List of lease offers
            
        Returns:
            ProcessedData: Processed data object
        """
        logger.info(f"Processing {len(offers)} lease offers")
        
        # Validate offers
        valid_offers = self._validate_offers(offers)
        logger.info(f"{len(valid_offers)}/{len(offers)} offers passed validation")
        
        # Transform data
        transformed_offers = self._transform_offers(valid_offers)
        
        # Create processed data object
        return ProcessedData(
            offers=transformed_offers,
            output_dir=self.output_dir
        )
    
    def _validate_offers(self, offers: List[LeaseOffer]) -> List[LeaseOffer]:
        """
        Validate lease offers.
        
        Args:
            offers (List[LeaseOffer]): List of lease offers
            
        Returns:
            List[LeaseOffer]: List of valid lease offers
        """
        valid_offers = []
        
        for offer in offers:
            try:
                # Basic validation is already done by Pydantic
                # Additional business logic validation can be added here
                valid_offers.append(offer)
            except Exception as e:
                logger.warning(f"Offer validation failed: {str(e)}")
        
        return valid_offers
    
    def _transform_offers(self, offers: List[LeaseOffer]) -> List[LeaseOffer]:
        """
        Transform lease offers.
        
        Args:
            offers (List[LeaseOffer]): List of lease offers
            
        Returns:
            List[LeaseOffer]: List of transformed lease offers
        """
        transformed_offers = []
        
        for offer in offers:
            # Apply transformations
            # This is where you would normalize data, enrich with additional info, etc.
            transformed_offers.append(offer)
        
        return transformed_offers


class ProcessedData:
    """
    Container for processed data with export capabilities.
    
    Attributes:
        offers (List[LeaseOffer]): Processed lease offers
        output_dir (Path): Directory for output files
    """
    
    def __init__(self, offers: List[LeaseOffer], output_dir: Path):
        """
        Initialize the processed data.
        
        Args:
            offers (List[LeaseOffer]): Processed lease offers
            output_dir (Path): Directory for output files
        """
        self.offers = offers
        self.output_dir = output_dir
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert offers to a list of dictionaries.
        
        Returns:
            List[Dict[str, Any]]: List of offer dictionaries
        """
        return [offer.to_dict() for offer in self.offers]
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert offers to a DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame of offers
        """
        return pd.DataFrame([offer.to_dict() for offer in self.offers])
    
    def save_to_json(self, filename: Optional[str] = None) -> Path:
        """
        Save offers to a JSON file.
        
        Args:
            filename (str, optional): Output filename
            
        Returns:
            Path: Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lease_offers_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(self.offers)} offers to {filepath}")
        return filepath
    
    def save_to_csv(self, filename: Optional[str] = None) -> Path:
        """
        Save offers to a CSV file.
        
        Args:
            filename (str, optional): Output filename
            
        Returns:
            Path: Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lease_offers_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Convert to DataFrame
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        
        logger.info(f"Saved {len(self.offers)} offers to {filepath}")
        return filepath
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the processed data.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not self.offers:
            return {"count": 0, "message": "No offers found"}
        
        # Convert to DataFrame for easy stats calculation
        df = self.to_dataframe()
        
        # Basic statistics
        summary = {
            "count": len(self.offers),
            "providers": df['provider'].nunique(),
            "car_makes": df['car_make'].nunique(),
            "price_range": {
                "min": df['monthly_price'].min(),
                "max": df['monthly_price'].max(),
                "avg": df['monthly_price'].mean(),
                "median": df['monthly_price'].median()
            },
            "top_makes": df['car_make'].value_counts().head(5).to_dict(),
            "scrape_timestamp": df['scrape_timestamp'].max()
        }
        
        return summary
    
    def __len__(self) -> int:
        """Get the number of offers."""
        return len(self.offers)