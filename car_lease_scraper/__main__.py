"""
Main entry point when the package is executed as a module.
"""

import asyncio
from car_lease_scraper.main import main

if __name__ == "__main__":
    asyncio.run(main())