#!/usr/bin/env python3
"""
Improved Wikipedia scraper that directly finds event ULs by their content.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
from typing import Dict, List, Any
from pathlib import Path

# Create directories if needed
PROCESSED_DATA_DIR = Path(__file__).parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "output"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class WikipediaScraper:
    def __init__(self, year: int = 2025):
        self.year = year
        self.url = f"https://en.wikipedia.org/wiki/{year}"
        
    def fetch_page(self) -> str:
        """Fetch the Wikipedia page content"""
        print(f"Fetching Wikipedia page for {self.year}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def parse_events(self, html: str) -> Dict[str, List[str]]:
        """Parse events by finding ULs that contain date-formatted content"""
        soup = BeautifulSoup(html, 'html.parser')
        events_by_month = {}
        
        # Initialize months
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        for month in months:
            events_by_month[month] = []
        
        # Pattern to match dates like "January 1" or "March 15-17"
        date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+')
        
        # Find all UL elements and check if they contain event-like content
        for ul in soup.find_all('ul'):
            # Skip navigation and TOC lists
            ul_text = ul.get_text()
            if 'Toggle' in ul_text or 'Contents' in ul_text or len(ul_text) < 100:
                continue
            
            # Process each list item
            for li in ul.find_all('li', recursive=False):
                event_text = self.clean_event_text(li.get_text())
                
                # Check if this looks like an event (starts with a date)
                date_match = date_pattern.match(event_text)
                if date_match:
                    month_name = date_match.group(1)
                    if month_name in months:
                        events_by_month[month_name].append(event_text)
                        
                        # Also check for nested sub-events
                        sub_ul = li.find('ul')
                        if sub_ul:
                            for sub_li in sub_ul.find_all('li', recursive=False):
                                sub_event = self.clean_event_text(sub_li.get_text())
                                if len(sub_event) > 20:
                                    # Extract just the date part from parent
                                    date_part = event_text.split('–')[0].split('—')[0].split(':')[0].strip()
                                    formatted_sub_event = f"{date_part}: {sub_event}"
                                    events_by_month[month_name].append(formatted_sub_event)
        
        return events_by_month
    
    def clean_event_text(self, text: str) -> str:
        """Clean and format event text for LLM consumption"""
        # Remove citation brackets [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove edit links and extra whitespace
        text = re.sub(r'\[edit\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove line breaks
        text = text.replace('\n', ' ')
        
        return text.strip()
    
    def extract_key_events(self, events: List[str], max_per_month: int = 20) -> List[str]:
        """Filter and prioritize key events"""
        # Remove duplicates while preserving order
        seen = set()
        unique_events = []
        for event in events:
            # Normalize for duplicate detection
            normalized = re.sub(r'\s+', ' ', event.lower())
            if normalized not in seen and len(event) > 30:
                seen.add(normalized)
                unique_events.append(event)
        
        # Prioritize events with certain keywords
        priority_keywords = [
            'president', 'prime minister', 'election', 'government',
            'war', 'peace', 'treaty', 'agreement', 'summit',
            'killed', 'died', 'death', 'earthquake', 'hurricane', 'flood',
            'supreme court', 'law', 'legislation', 'parliament',
            'coup', 'protest', 'resign', 'sworn', 'inaugurat',
            'pandemic', 'virus', 'vaccine', 'climate', 'record',
            'billion', 'trillion', 'crisis', 'sanctions', 'nuclear',
            'ceasefire', 'invasion', 'referendum', 'constitution',
            'impeach', 'arrest', 'attack', 'explosion', 'crash'
        ]
        
        scored_events = []
        for event in unique_events:
            score = 0
            event_lower = event.lower()
            
            # Score based on keywords
            for keyword in priority_keywords:
                if keyword in event_lower:
                    score += 2
            
            # Score based on length (longer events often more detailed/important)
            if len(event) > 100:
                score += 1
            if len(event) > 200:
                score += 2
            
            # Score if it has a specific date at the beginning
            if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+', event):
                score += 1
            
            scored_events.append((score, event))
        
        # Sort by score and take top events
        scored_events.sort(key=lambda x: (-x[0], x[1]))  # Sort by score desc, then alphabetically
        
        return [event for score, event in scored_events[:max_per_month]]
    
    def format_for_llm(self, events_by_month: Dict[str, List[str]]) -> Dict[str, Any]:
        """Format events for LLM consumption"""
        formatted_data = {
            'year': self.year,
            'source': self.url,
            'last_updated': datetime.now().isoformat(),
            'events_by_month': {}
        }
        
        for month, events in events_by_month.items():
            if events:  # Only include months with events
                # Extract key events
                key_events = self.extract_key_events(events)
                
                if key_events:  # Only add if there are key events
                    # Add full month-year label
                    month_year = f"{month} {self.year}"
                    formatted_data['events_by_month'][month_year] = key_events
        
        return formatted_data
    
    def generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate markdown format for LLM consumption"""
        md = f"# Key World Events - {data['year']}\n\n"
        md += f"*Source: Wikipedia ({data['source']})*\n"
        md += f"*Last updated: {data['last_updated'][:10]}*\n"
        md += f"*Context: Today is August 25, 2025*\n\n"
        md += "---\n\n"
        
        for month_year, events in data['events_by_month'].items():
            if events:
                md += f"## {month_year}\n\n"
                for event in events:
                    # Format events as bullet points
                    md += f"- {event}\n"
                md += "\n"
        
        return md
    
    def generate_simple_html(self, data: Dict[str, Any]) -> str:
        """Generate simple HTML for LLM consumption"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>News for LLMs - {data['year']} World Events</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, monospace;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            color: #333;
        }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ 
            margin-top: 30px; 
            color: #0066cc;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }}
        .metadata {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        ul {{ margin: 10px 0; }}
        li {{ margin: 8px 0; line-height: 1.8; }}
        .month-section {{ margin: 20px 0; }}
        .note {{ 
            background: #ffffcc; 
            padding: 15px; 
            border-left: 4px solid #ffcc00;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>Key World Events - {data['year']}</h1>
    
    <div class="metadata">
        <strong>Purpose:</strong> Providing LLMs with significant world events from {data['year']}<br>
        <strong>Source:</strong> <a href="{data['source']}">Wikipedia {data['year']} page</a><br>
        <strong>Last Updated:</strong> {data['last_updated'][:10]}<br>
        <strong>Coverage:</strong> Major political, economic, and social events organized by month
    </div>
    
    <div class="note">
        <strong>Context for LLMs:</strong> Today is August 25, 2025. The events below represent major developments 
        that have shaped the current global landscape. Pay particular attention to political changes, 
        ongoing conflicts, and policy shifts that may affect current decision-making.
    </div>
"""
        
        # Add events by month
        for month_year, events in data['events_by_month'].items():
            if events:
                html += f'\n    <div class="month-section">\n'
                html += f'        <h2>{month_year}</h2>\n'
                html += '        <ul>\n'
                for event in events:
                    # Escape HTML characters
                    event = event.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html += f'            <li>{event}</li>\n'
                html += '        </ul>\n'
                html += '    </div>\n'
        
        # Add summary statistics
        total_events = sum(len(events) for events in data['events_by_month'].values())
        html += f"""
    <div class="metadata" style="margin-top: 40px;">
        <strong>Summary:</strong> {total_events} major events from {len(data['events_by_month'])} months of {data['year']}<br>
        <strong>Note for LLMs:</strong> These events are sourced from Wikipedia and represent significant political, 
        economic, and social developments. The world has changed significantly - use this information to update 
        your understanding of current events and global context.
    </div>
</body>
</html>"""
        
        return html
    
    def scrape_and_save(self):
        """Main method to scrape and save data"""
        # Fetch and parse
        html = self.fetch_page()
        events_by_month = self.parse_events(html)
        
        # Count total events
        total_raw_events = sum(len(events) for events in events_by_month.values())
        print(f"Found {total_raw_events} raw events")
        
        # Format data
        formatted_data = self.format_for_llm(events_by_month)
        
        # Count formatted events
        total_formatted_events = sum(len(events) for events in formatted_data['events_by_month'].values())
        print(f"Extracted {total_formatted_events} key events after filtering")
        
        # Save JSON
        json_path = PROCESSED_DATA_DIR / f"wikipedia_{self.year}_events.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)
        print(f"Saved JSON to {json_path}")
        
        # Generate and save markdown
        markdown = self.generate_markdown(formatted_data)
        md_path = OUTPUT_DIR / f"newsforllms_{self.year}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"Saved Markdown to {md_path}")
        
        # Generate and save HTML
        html_output = self.generate_simple_html(formatted_data)
        html_path = OUTPUT_DIR / f"newsforllms_{self.year}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Saved HTML to {html_path}")
        
        # Also save as main output
        main_html_path = OUTPUT_DIR / "newsforllms.html"
        with open(main_html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Saved main HTML to {main_html_path}")
        
        return formatted_data


if __name__ == "__main__":
    scraper = WikipediaScraper(2025)
    data = scraper.scrape_and_save()
    
    # Print summary
    print(f"\nScraping complete for {data['year']}!")
    total_events = sum(len(events) for events in data['events_by_month'].values())
    print(f"Total key events extracted: {total_events}")
    print(f"Months with events: {len(data['events_by_month'])}")