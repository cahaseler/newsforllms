import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from pathlib import Path
import openai
from collections import defaultdict
import re

from config import (
    OPENAI_API_KEY, 
    CATEGORIES, 
    DATABASE_FILE,
    PROCESSED_DATA_DIR,
    SUMMARY_LENGTH
)

class NewsProcessor:
    def __init__(self):
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            print("Warning: OpenAI API key not found. Summarization will use fallback method.")
            self.client = None
    
    def load_database(self) -> Dict[str, Any]:
        """Load the news database"""
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE, 'r') as f:
                return json.load(f)
        return {'articles': {}, 'last_updated': None}
    
    def filter_recent_articles(self, articles: Dict[str, Any], days: int = 365) -> List[Dict[str, Any]]:
        """Filter articles from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_articles = []
        
        for article_id, article in articles.items():
            pub_date = datetime.fromisoformat(article['published'])
            if pub_date > cutoff_date:
                recent_articles.append(article)
        
        # Sort by date (newest first)
        recent_articles.sort(key=lambda x: x['published'], reverse=True)
        
        return recent_articles
    
    def categorize_article(self, article: Dict[str, Any]) -> List[str]:
        """Categorize an article based on its content"""
        text = f"{article['title']} {article['description']} {article.get('content', '')}"
        text_lower = text.lower()
        
        tags = []
        
        # Keywords for each category
        category_keywords = {
            "Politics": ["election", "vote", "parliament", "congress", "president", "minister", "government", "political", "democrat", "republican", "party"],
            "Geopolitics": ["sanctions", "diplomacy", "summit", "nato", "un", "treaty", "alliance", "conflict", "tension"],
            "Elections": ["election", "ballot", "voting", "campaign", "candidate", "polls", "primary", "electoral"],
            "Policy Changes": ["policy", "reform", "legislation", "regulation", "law", "bill", "act", "amendment"],
            "International Relations": ["bilateral", "multilateral", "foreign", "ambassador", "embassy", "diplomatic", "international"],
            "Economic Policy": ["economy", "inflation", "gdp", "budget", "fiscal", "monetary", "tax", "trade", "tariff"],
            "Climate & Environment": ["climate", "carbon", "emissions", "renewable", "sustainability", "environment", "cop28", "green"],
            "Technology & AI": ["artificial intelligence", "ai", "technology", "tech", "digital", "cyber", "data", "algorithm"],
            "Military & Defense": ["military", "defense", "weapon", "army", "navy", "air force", "nato", "pentagon"],
            "Social Movements": ["protest", "movement", "activism", "rights", "equality", "justice", "demonstration"],
            "Legal & Courts": ["court", "judge", "legal", "lawsuit", "ruling", "verdict", "justice", "constitutional"],
            "Public Health": ["health", "pandemic", "vaccine", "disease", "healthcare", "medical", "hospital", "covid"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(category)
        
        # If no tags found, add general Politics tag if it seems political
        if not tags and article['category'] in ['politics', 'world']:
            tags.append("Politics")
        
        return tags[:3]  # Limit to 3 tags per article
    
    def summarize_article_llm(self, article: Dict[str, Any]) -> str:
        """Summarize article using OpenAI API"""
        if not self.client:
            return self.summarize_article_fallback(article)
        
        try:
            prompt = f"""Summarize this news article in 2-3 sentences for an LLM that needs to understand recent world events. 
Focus on the key facts, political implications, and why this matters globally.

Title: {article['title']}
Description: {article['description']}
Content: {article.get('content', '')[:1000]}

Summary (2-3 sentences, focusing on facts and implications):"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a news summarizer creating concise, factual summaries for LLMs to understand recent world events."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error summarizing with LLM: {e}")
            return self.summarize_article_fallback(article)
    
    def summarize_article_fallback(self, article: Dict[str, Any]) -> str:
        """Fallback summarization without LLM"""
        # Clean and truncate description
        description = article['description']
        description = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Create a simple summary
        if len(description) > 200:
            # Find sentence boundaries
            sentences = description.split('. ')
            summary = '. '.join(sentences[:2]) + '.'
        else:
            summary = description
        
        # Add date context
        pub_date = datetime.fromisoformat(article['published'])
        date_str = pub_date.strftime("%B %d, %Y")
        
        return f"{summary} (Published: {date_str})"
    
    def deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Create normalized title for comparison
            normalized_title = re.sub(r'[^a-z0-9]', '', article['title'].lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
        
        return unique_articles
    
    def group_by_month(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group articles by month"""
        grouped = defaultdict(list)
        
        for article in articles:
            pub_date = datetime.fromisoformat(article['published'])
            month_key = pub_date.strftime("%Y-%m")
            month_label = pub_date.strftime("%B %Y")
            
            grouped[month_label].append(article)
        
        # Sort months (most recent first)
        sorted_groups = dict(sorted(grouped.items(), 
                                  key=lambda x: datetime.strptime(x[0], "%B %Y"), 
                                  reverse=True))
        
        return sorted_groups
    
    def process_articles(self, limit: int = 100) -> Dict[str, Any]:
        """Main processing pipeline"""
        print("Loading database...")
        db = self.load_database()
        
        print("Filtering recent articles...")
        recent_articles = self.filter_recent_articles(db['articles'])
        
        print(f"Deduplicating {len(recent_articles)} articles...")
        unique_articles = self.deduplicate_articles(recent_articles)
        
        # Limit to most recent N articles for processing
        articles_to_process = unique_articles[:limit]
        
        print(f"Processing {len(articles_to_process)} articles...")
        processed_articles = []
        
        for i, article in enumerate(articles_to_process):
            if i % 10 == 0:
                print(f"  Processing article {i+1}/{len(articles_to_process)}...")
            
            # Add categorization
            article['tags'] = self.categorize_article(article)
            
            # Add summary
            article['summary'] = self.summarize_article_llm(article)
            
            processed_articles.append(article)
        
        # Group by month
        grouped_articles = self.group_by_month(processed_articles)
        
        # Save processed data
        output_file = PROCESSED_DATA_DIR / "processed_articles.json"
        processed_data = {
            'articles': processed_articles,
            'grouped_by_month': {month: [a['id'] for a in articles] 
                                for month, articles in grouped_articles.items()},
            'processed_at': datetime.now().isoformat(),
            'total_count': len(processed_articles)
        }
        
        with open(output_file, 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        print(f"Saved processed data to {output_file}")
        
        return grouped_articles


if __name__ == "__main__":
    processor = NewsProcessor()
    grouped_articles = processor.process_articles(limit=50)
    
    print("\nProcessing complete!")
    print(f"Months covered: {list(grouped_articles.keys())}")
    for month, articles in grouped_articles.items():
        print(f"  {month}: {len(articles)} articles")