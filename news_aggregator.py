import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import hashlib
from pathlib import Path
import time

from config import NEWS_SOURCES, RAW_DATA_DIR

class NewsAggregator:
    def __init__(self):
        self.articles = []
        self.seen_urls = set()
        
    def fetch_rss_feed(self, feed_url: str, source_name: str, category: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries:
                # Skip if we've seen this URL
                if entry.link in self.seen_urls:
                    continue
                    
                self.seen_urls.add(entry.link)
                
                # Parse publish date
                published = None
                if hasattr(entry, 'published_parsed'):
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed'):
                    published = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                else:
                    published = datetime.now()
                
                # Only include articles from the last year
                if published < datetime.now() - timedelta(days=365):
                    continue
                
                article = {
                    'id': hashlib.md5(entry.link.encode()).hexdigest(),
                    'title': entry.title,
                    'url': entry.link,
                    'source': source_name,
                    'category': category,
                    'published': published.isoformat(),
                    'description': entry.get('summary', ''),
                    'content': entry.get('content', [{}])[0].get('value', '') if hasattr(entry, 'content') else '',
                    'fetched_at': datetime.now().isoformat()
                }
                
                articles.append(article)
                
            return articles
            
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            return []
    
    def fetch_all_sources(self) -> List[Dict[str, Any]]:
        """Fetch news from all configured sources"""
        all_articles = []
        
        for source_name, feeds in NEWS_SOURCES.items():
            print(f"Fetching from {source_name}...")
            
            for category, feed_url in feeds.items():
                articles = self.fetch_rss_feed(feed_url, source_name, category)
                all_articles.extend(articles)
                print(f"  - {category}: {len(articles)} articles")
                
                # Be polite to servers
                time.sleep(1)
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x['published'], reverse=True)
        
        return all_articles
    
    def save_raw_articles(self, articles: List[Dict[str, Any]]):
        """Save raw articles to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RAW_DATA_DIR / f"raw_articles_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(articles, f, indent=2)
        
        print(f"Saved {len(articles)} articles to {output_file}")
        
        # Also save as latest for easy access
        latest_file = RAW_DATA_DIR / "latest_raw_articles.json"
        with open(latest_file, 'w') as f:
            json.dump(articles, f, indent=2)
        
        return output_file
    
    def load_existing_database(self, db_path: Path) -> Dict[str, Any]:
        """Load existing news database"""
        if db_path.exists():
            with open(db_path, 'r') as f:
                return json.load(f)
        return {'articles': {}, 'last_updated': None}
    
    def merge_with_database(self, new_articles: List[Dict[str, Any]], db_path: Path) -> Dict[str, Any]:
        """Merge new articles with existing database"""
        db = self.load_existing_database(db_path)
        
        # Convert list to dict keyed by article ID
        for article in new_articles:
            article_id = article['id']
            if article_id not in db['articles']:
                db['articles'][article_id] = article
        
        db['last_updated'] = datetime.now().isoformat()
        
        # Save updated database
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2)
        
        print(f"Database now contains {len(db['articles'])} unique articles")
        
        return db


if __name__ == "__main__":
    aggregator = NewsAggregator()
    
    print("Starting news aggregation...")
    articles = aggregator.fetch_all_sources()
    
    print(f"\nTotal articles fetched: {len(articles)}")
    
    # Save raw articles
    aggregator.save_raw_articles(articles)
    
    # Merge with database
    from config import DATABASE_FILE
    db = aggregator.merge_with_database(articles, DATABASE_FILE)
    
    print("\nAggregation complete!")