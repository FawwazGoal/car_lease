"""
Scraper Registry

Provides a registry for discovering and managing scrapers.
"""

import importlib
import inspect
from typing import Dict, List, Type, Any

from car_lease_scraper.core.base_scraper import BaseScraper
from car_lease_scraper.utils.logging import get_logger


# Initialize logger
logger = get_logger("scraper_registry")


class ScraperRegistry:
    """
    Registry for managing and discovering scrapers.
    
    Maintains a mapping of provider names to scraper classes.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
    
    def register(self, scraper_class: Type[BaseScraper]):
        """
        Register a scraper class.
        
        Args:
            scraper_class (Type[BaseScraper]): Scraper class to register
        """
        if not issubclass(scraper_class, BaseScraper):
            raise TypeError(f"{scraper_class.__name__} is not a subclass of BaseScraper")
        
        provider_name = scraper_class.provider_name
        if not provider_name:
            raise ValueError(f"{scraper_class.__name__} has no provider_name defined")
        
        self._scrapers[provider_name] = scraper_class
        logger.debug(f"Registered scraper for provider: {provider_name}")
    
    def get_scraper(self, provider_name: str) -> Type[BaseScraper]:
        """
        Get a scraper class by provider name.
        
        Args:
            provider_name (str): Provider name
            
        Returns:
            Type[BaseScraper]: Scraper class
            
        Raises:
            KeyError: If no scraper is registered for the provider
        """
        if provider_name not in self._scrapers:
            raise KeyError(f"No scraper registered for provider: {provider_name}")
        
        return self._scrapers[provider_name]
    
    def list_providers(self) -> List[str]:
        """
        Get a list of registered provider names.
        
        Returns:
            List[str]: List of provider names
        """
        return list(self._scrapers.keys())
    
    def get_provider_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered providers.
        
        Returns:
            List[Dict[str, Any]]: List of provider information
        """
        return [
            {
                "name": provider_name,
                "scraper": scraper_class.__name__,
                "url": scraper_class.base_url
            }
            for provider_name, scraper_class in self._scrapers.items()
        ]
    
    def discover_scrapers(self):
        """Automatically discover and register scrapers."""
        # Import scrapers module to make sure all scrapers are loaded
        import car_lease_scraper.scrapers
        
        # Get all modules in the scrapers package
        package = car_lease_scraper.scrapers
        module_names = [
            name for name in dir(package) 
            if not name.startswith('_') and name != 'registry'
        ]
        
        # Import each module and register scraper classes
        for module_name in module_names:
            try:
                module = importlib.import_module(f"car_lease_scraper.scrapers.{module_name}")
                
                # Find all scraper classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseScraper) and 
                        obj is not BaseScraper and 
                        obj.provider_name):
                        self.register(obj)
                
            except ImportError as e:
                logger.error(f"Error importing module {module_name}: {str(e)}")


# Create global registry instance
registry = ScraperRegistry()