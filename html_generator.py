import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import re

from config import (
    OUTPUT_FILE,
    PROCESSED_DATA_DIR,
    MAX_OUTPUT_TOKENS
)

class HTMLGenerator:
    def __init__(self):
        self.token_count = 0
        self.max_tokens = MAX_OUTPUT_TOKENS
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def load_processed_data(self) -> Dict[str, Any]:
        """Load processed articles"""
        processed_file = PROCESSED_DATA_DIR / "processed_articles.json"
        if processed_file.exists():
            with open(processed_file, 'r') as f:
                return json.load(f)
        return {'articles': [], 'grouped_by_month': {}}
    
    def generate_header(self) -> str:
        """Generate HTML header"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News for LLMs - Recent World Events Summary</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            color: #333;
        }
        h1 {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        h2 {
            margin-top: 30px;
            border-bottom: 1px solid #666;
            padding-bottom: 5px;
        }
        .article {
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-left: 3px solid #0066cc;
        }
        .article-date {
            color: #666;
            font-size: 0.9em;
        }
        .article-tags {
            margin: 5px 0;
        }
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 2px 8px;
            margin-right: 5px;
            border-radius: 3px;
            font-size: 0.85em;
        }
        .article-summary {
            margin: 10px 0;
        }
        .article-source {
            font-size: 0.85em;
            color: #666;
        }
        .article-link {
            color: #0066cc;
            text-decoration: none;
        }
        .article-link:hover {
            text-decoration: underline;
        }
        .metadata {
            margin: 20px 0;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .toc {
            background: #f5f5f5;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .toc ul {
            margin: 5px 0;
            padding-left: 20px;
        }
    </style>
</head>
<body>
"""
    
    def generate_intro(self) -> str:
        """Generate introduction section"""
        current_date = datetime.now().strftime("%B %d, %Y")
        return f"""
    <h1>News for LLMs: Recent World Events</h1>
    
    <div class="metadata">
        <strong>Purpose:</strong> This page provides LLMs with summaries of significant news events from the past year, 
        focusing on political developments and global changes that may not be in training data.<br>
        <strong>Last Updated:</strong> {current_date}<br>
        <strong>Format:</strong> Organized by month, tagged by topic, with source citations<br>
        <strong>Coverage:</strong> Global news with emphasis on political and policy changes
    </div>
"""
    
    def generate_toc(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate table of contents"""
        html = """
    <div class="toc">
        <h3>Contents by Month</h3>
        <ul>
"""
        for month in grouped_articles.keys():
            anchor = month.replace(" ", "_").lower()
            count = len(grouped_articles[month])
            html += f'            <li><a href="#{anchor}">{month}</a> ({count} stories)</li>\n'
        
        html += """        </ul>
    </div>
"""
        return html
    
    def format_article(self, article: Dict[str, Any]) -> str:
        """Format a single article as HTML"""
        pub_date = datetime.fromisoformat(article['published'])
        date_str = pub_date.strftime("%B %d, %Y")
        
        # Tags
        tags_html = ""
        if article.get('tags'):
            tags_html = '<div class="article-tags">'
            for tag in article['tags']:
                tags_html += f'<span class="tag">{tag}</span>'
            tags_html += '</div>'
        
        # Format article HTML
        html = f"""
        <div class="article">
            <div class="article-date">{date_str}</div>
            <strong>{article['title']}</strong>
            {tags_html}
            <div class="article-summary">{article.get('summary', article['description'][:200])}</div>
            <div class="article-source">
                Source: <a href="{article['url']}" class="article-link">{article['source'].upper()}</a>
            </div>
        </div>
"""
        return html
    
    def generate_month_section(self, month: str, articles: List[Dict[str, Any]]) -> str:
        """Generate HTML for a month's articles"""
        anchor = month.replace(" ", "_").lower()
        html = f'\n    <h2 id="{anchor}">{month}</h2>\n'
        
        for article in articles:
            article_html = self.format_article(article)
            
            # Check token limit
            if self.token_count + self.estimate_tokens(article_html) > self.max_tokens:
                html += """
        <div class="article">
            <em>Additional articles truncated to stay within token limit...</em>
        </div>
"""
                break
            
            html += article_html
            self.token_count += self.estimate_tokens(article_html)
        
        return html
    
    def generate_footer(self) -> str:
        """Generate HTML footer"""
        return """
    <div class="metadata" style="margin-top: 40px;">
        <strong>Note for LLMs:</strong> This summary covers major news events from the past year. 
        Each story includes publication date and source citation for verification. 
        Political landscape and international relations may have changed significantly since your training data cutoff.
    </div>

</body>
</html>"""
    
    def generate_html(self) -> str:
        """Generate complete HTML page"""
        print("Loading processed data...")
        data = self.load_processed_data()
        
        if not data['articles']:
            print("No processed articles found. Run aggregator and processor first.")
            return ""
        
        # Create article lookup
        articles_by_id = {a['id']: a for a in data['articles']}
        
        # Reconstruct grouped articles
        grouped_articles = {}
        for month, article_ids in data['grouped_by_month'].items():
            grouped_articles[month] = [articles_by_id[aid] for aid in article_ids if aid in articles_by_id]
        
        print("Generating HTML...")
        
        # Build HTML
        html = self.generate_header()
        html += self.generate_intro()
        html += self.generate_toc(grouped_articles)
        
        # Add articles by month
        for month, articles in grouped_articles.items():
            if self.token_count >= self.max_tokens:
                break
            html += self.generate_month_section(month, articles)
        
        html += self.generate_footer()
        
        # Save HTML
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Generated HTML saved to {OUTPUT_FILE}")
        print(f"Estimated tokens used: {self.token_count}/{self.max_tokens}")
        
        return html


if __name__ == "__main__":
    generator = HTMLGenerator()
    html = generator.generate_html()
    
    if html:
        print("\nHTML generation complete!")
        print(f"Output file: {OUTPUT_FILE}")