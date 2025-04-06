"""
Main Entry Point

Provides the main entry point for the car lease scraper application.
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from car_lease_scraper.scrapers.registry import registry
from car_lease_scraper.pipeline.processor import DataProcessor
from car_lease_scraper.utils.logging import setup_root_logger, get_logger
from car_lease_scraper.config import SETTINGS


# Initialize console and logger
console = Console()
logger = get_logger("main")


async def run_scraper(
    provider_name: str,
    output_formats: List[str],
    output_dir: Optional[Path] = None,
    headless: bool = True,
    max_pages: int = 5
) -> bool:
    """
    Run a scraper for a specific provider.
    
    Args:
        provider_name (str): Name of the provider to scrape
        output_formats (List[str]): List of output formats (json, csv)
        output_dir (Path, optional): Directory for output files
        headless (bool): Whether to run browser in headless mode
        max_pages (int): Maximum number of pages to scrape
        
    Returns:
        bool: Whether the scraping was successful
    """
    try:
        # Get the scraper class from the registry
        scraper_class = registry.get_scraper(provider_name)
        
        # Create scraper instance
        scraper = scraper_class(headless=headless, max_pages=max_pages)
        
        # Create processor
        processor = DataProcessor(output_dir=output_dir)
        
        # Print scraping start info
        console.print(f"[bold green]Starting scraper for {provider_name}[/bold green]")
        console.print(f"Target URL: [blue]{scraper.base_url}[/blue]")
        
        start_time = datetime.now()
        
        # Run the scraper
        async with scraper:
            # Extract data
            offers = await scraper.scrape()
            
            if not offers:
                console.print("[bold yellow]No offers found[/bold yellow]")
                return False
            
            # Process data
            processed_data = processor.process(offers)
            
            # Save data in requested formats
            for output_format in output_formats:
                if output_format.lower() == 'json':
                    filepath = processed_data.save_to_json()
                    console.print(f"Saved JSON data to: [blue]{filepath}[/blue]")
                
                elif output_format.lower() == 'csv':
                    filepath = processed_data.save_to_csv()
                    console.print(f"Saved CSV data to: [blue]{filepath}[/blue]")
            
            # Print summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            console.print("\n[bold]Scraping Summary:[/bold]")
            console.print(f"Total offers: [green]{len(processed_data)}[/green]")
            console.print(f"Duration: [green]{duration:.2f} seconds[/green]")
            
            # Show sample of scraped data
            if offers:
                table = Table(title="Sample of Scraped Data")
                table.add_column("Make/Model", style="cyan")
                table.add_column("Version", style="magenta")
                table.add_column("Price", style="green")
                table.add_column("Term", style="yellow")
                table.add_column("Kilometers", style="yellow")
                
                for offer in offers[:5]:  # Show first 5 offers
                    table.add_row(
                        f"{offer.car_make} {offer.car_model}",
                        offer.version or "N/A",
                        f"€{offer.monthly_price:.2f}",
                        f"{offer.lease_term_months} months",
                        f"{offer.kilometers_per_year:,} km/year"
                    )
                
                console.print(table)
            
            return True
    
    except KeyError:
        console.print(f"[bold red]Error: Provider '{provider_name}' not found[/bold red]")
        return False
    
    except Exception as e:
        console.print(f"[bold red]Error during scraping: {str(e)}[/bold red]")
        logger.exception("Scraping failed")
        return False


def list_providers():
    """List all available providers."""
    providers = registry.get_provider_info()
    
    if not providers:
        console.print("[yellow]No providers registered[/yellow]")
        return
    
    table = Table(title="Available Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Scraper", style="green")
    table.add_column("URL", style="blue")
    
    for provider in providers:
        table.add_row(
            provider["name"],
            provider["scraper"],
            provider["url"]
        )
    
    console.print(table)


async def main():
    """Main entry point function."""
    # Set up logging
    setup_root_logger()
    
    # Discover available scrapers
    registry.discover_scrapers()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Car Lease Scraper")
    parser.add_argument(
        "--provider", "-p",
        help="Provider to scrape (use --list to see available providers)"
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true",
        help="List available providers"
    )
    parser.add_argument(
        "--output-format", "-f",
        default="json",
        help="Output format(s), comma-separated (json,csv)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=str(SETTINGS.output_dir),
        help="Output directory"
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        default=SETTINGS.headless,
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=SETTINGS.max_pages,
        help="Maximum number of pages to scrape"
    )
    
    args = parser.parse_args()
    
    # List providers if requested
    if args.list:
        list_providers()
        return
    
    # Check if provider is specified
    if not args.provider:
        parser.print_help()
        return
    
    # Run scraper
    output_formats = [fmt.strip() for fmt in args.output_format.split(",")]
    success = await run_scraper(
        provider_name=args.provider,
        output_formats=output_formats,
        output_dir=Path(args.output_dir),
        headless=args.headless,
        max_pages=args.max_pages
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())