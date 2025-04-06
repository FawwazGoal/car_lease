"""
Setup script for car-lease-scraper package.
"""

from setuptools import setup, find_packages

setup(
    name="car-lease-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.30.0",
        "pydantic>=1.10.0",
        "pandas>=1.5.0",
        "rich>=12.0.0",
        "tenacity>=8.0.0",
        "python-dotenv>=0.21.0"
    ],
    entry_points={
        "console_scripts": [
            "car-lease-scraper=car_lease_scraper.main:main"
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A modular web scraping solution for collecting car leasing offers",
    keywords="web-scraping, car-leasing, data-extraction",
    python_requires=">=3.8",
)