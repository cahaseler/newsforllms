#!/usr/bin/env python3
"""
Main pipeline script to run the complete news aggregation and generation process.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from news_aggregator import NewsAggregator
from news_processor import NewsProcessor
from html_generator import HTMLGenerator
from config import DATABASE_FILE, OUTPUT_FILE

def main():
    print("=" * 60)
    print("News for LLMs - Pipeline Runner")
    print("=" * 60)
    
    # Step 1: Aggregate news
    print("\n[1/3] Aggregating news from sources...")
    aggregator = NewsAggregator()
    articles = aggregator.fetch_all_sources()
    
    if not articles:
        print("No articles fetched. Check your internet connection and RSS feeds.")
        return
    
    aggregator.save_raw_articles(articles)
    db = aggregator.merge_with_database(articles, DATABASE_FILE)
    
    # Step 2: Process articles
    print("\n[2/3] Processing articles (categorization & summarization)...")
    processor = NewsProcessor()
    grouped_articles = processor.process_articles(limit=100)
    
    # Step 3: Generate HTML
    print("\n[3/3] Generating HTML output...")
    generator = HTMLGenerator()
    html = generator.generate_html()
    
    if html:
        print("\n" + "=" * 60)
        print("Pipeline completed successfully!")
        print(f"Output file: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\nPipeline completed with warnings. Check the logs above.")

if __name__ == "__main__":
    main()