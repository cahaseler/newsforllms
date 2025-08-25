#!/usr/bin/env python3
"""
Simple runner for Wikipedia scraping approach.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from wikipedia_scraper import WikipediaScraper

def main():
    # Determine which year to scrape
    current_year = datetime.now().year
    
    print("=" * 60)
    print(f"News for LLMs - Wikipedia Scraper")
    print("=" * 60)
    
    # Scrape current year
    print(f"\nScraping events for {current_year}...")
    scraper = WikipediaScraper(current_year)
    data = scraper.scrape_and_save()
    
    # Print summary
    total_events = sum(len(events) for events in data['events_by_month'].values())
    
    print("\n" + "=" * 60)
    print("Scraping completed successfully!")
    print(f"Year: {current_year}")
    print(f"Total events: {total_events}")
    print(f"Output files:")
    print(f"  - output/newsforllms.html (main)")
    print(f"  - output/newsforllms_{current_year}.html")
    print(f"  - output/newsforllms_{current_year}.md")
    print("=" * 60)

if __name__ == "__main__":
    main()