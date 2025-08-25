#!/usr/bin/env python3
"""
Improved Wikipedia scraper that directly finds event ULs by their content.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
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
    
    def parse_events(self, html: str) -> Dict[str, List[Dict]]:
        """Parse events by finding ULs that contain date-formatted content"""
        soup = BeautifulSoup(html, 'html.parser')
        events_by_month = {}
        
        # Build references lookup first
        references = self.build_references_lookup(soup)
        
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
                # Extract citations before removing nested content
                citations = self.extract_citations(li, references)
                
                # Check if this li has nested sub-events
                sub_ul = li.find('ul')
                if sub_ul:
                    # Remove the sub-ul from the li to get just the main event text
                    sub_ul.extract()
                
                # Now get the clean main event text
                event_text = self.clean_event_text(li.get_text())
                
                # Check if this looks like an event (starts with a date)
                date_match = date_pattern.match(event_text)
                if date_match:
                    month_name = date_match.group(1)
                    if month_name in months:
                        # Only include events that have already occurred
                        if self.is_past_event(event_text):
                            event_data = {
                                'text': event_text,
                                'citations': citations
                            }
                            events_by_month[month_name].append(event_data)
        
        return events_by_month
    
    def build_references_lookup(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """Build a lookup table of reference IDs to their content"""
        references = {}
        
        # Find all reference list items
        for ref_li in soup.find_all('li', id=re.compile(r'^cite_note-\d+')):
            ref_id = ref_li.get('id', '')
            
            # Extract citation info
            cite_elem = ref_li.find('cite')
            if cite_elem:
                # Get the source text
                source_text = cite_elem.get_text().strip()
                
                # Try to find URL
                url = None
                for link in ref_li.find_all('a', class_='external'):
                    if 'href' in link.attrs:
                        url = link['href']
                        break
                
                references[ref_id] = {
                    'text': source_text,
                    'url': url
                }
        
        return references
    
    def is_past_event(self, event_text: str) -> bool:
        """Check if an event has already occurred based on today being August 25, 2025"""
        current_date = date(2025, 8, 25)  # Today is August 25, 2025
        
        # Extract date from event text (e.g., "January 10", "March 15-17")
        date_match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)', event_text)
        if not date_match:
            return True  # If we can't parse the date, include it
        
        month_name = date_match.group(1)
        day = int(date_match.group(2))
        
        # Convert month name to number
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month_num = month_map.get(month_name)
        if not month_num:
            return True  # If we can't parse the month, include it
        
        try:
            event_date = date(2025, month_num, day)
            return event_date <= current_date
        except ValueError:
            # Invalid date (e.g., February 30), include it
            return True
    
    def extract_citations(self, li_element, references: Dict[str, Dict]) -> List[Dict]:
        """Extract citations from a list item"""
        citations = []
        
        # Find all citation superscripts in this li
        for sup in li_element.find_all('sup', class_='reference'):
            link = sup.find('a')
            if link and 'href' in link.attrs:
                # Get the reference ID from the href (e.g., #cite_note-18 -> cite_note-18)
                ref_id = link['href'].replace('#', '')
                
                # Look up the full citation
                if ref_id in references:
                    citations.append(references[ref_id])
        
        return citations
    
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
    
    def extract_key_events(self, events: List[Dict], max_per_month: int = 20) -> List[Dict]:
        """Remove duplicates from events"""
        # Remove duplicates while preserving order
        seen = set()
        unique_events = []
        for event in events:
            # Normalize for duplicate detection
            event_text = event['text'] if isinstance(event, dict) else event
            normalized = re.sub(r'\s+', ' ', event_text.lower())
            if normalized not in seen and len(event_text) > 30:
                seen.add(normalized)
                unique_events.append(event)
        
        return unique_events
    
    def format_for_llm(self, events_by_month: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Format events for LLM consumption"""
        formatted_data = {
            'year': self.year,
            'source': self.url,
            'last_updated': datetime.now().isoformat(),
            'events_by_month': {}
        }
        
        for month, events in events_by_month.items():
            if events:  # Only include months with events
                # Remove duplicates
                unique_events = self.extract_key_events(events)
                
                if unique_events:  # Only add if there are events
                    # Add full month-year label
                    month_year = f"{month} {self.year}"
                    formatted_data['events_by_month'][month_year] = unique_events
        
        return formatted_data
    
    def generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate markdown format for LLM consumption"""
        md = f"# World Events - {data['year']}\n\n"
        md += f"*Source: Wikipedia ({data['source']})*\n"
        md += f"*Last updated: {data['last_updated'][:10]}*\n"
        md += f"*Context: Today is August 25, 2025*\n\n"
        md += "---\n\n"
        
        for month_year, events in data['events_by_month'].items():
            if events:
                md += f"## {month_year}\n\n"
                for event in events:
                    # Format events as bullet points
                    if isinstance(event, dict):
                        md += f"- {event['text']}"
                        # Add citations if available
                        if event.get('citations'):
                            md += " ["
                            for i, cite in enumerate(event['citations']):
                                if i > 0:
                                    md += "; "
                                if cite.get('url'):
                                    md += f"[{cite['text'][:50]}...]({cite['url']})"
                                else:
                                    md += cite['text'][:50] + "..."
                            md += "]"
                        md += "\n"
                    else:
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
    <h1>World Events - {data['year']}</h1>
    
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
                    if isinstance(event, dict):
                        # Escape HTML characters
                        event_text = event['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html += f'            <li>{event_text}'
                        
                        # Add citations if available
                        if event.get('citations'):
                            html += ' <small style="color: #666;">['
                            for i, cite in enumerate(event['citations']):
                                if i > 0:
                                    html += '; '
                                if cite.get('url'):
                                    html += f'<a href="{cite["url"]}" target="_blank">{cite["text"][:30]}...</a>'
                                else:
                                    html += cite['text'][:30] + '...'
                            html += ']</small>'
                        html += '</li>\n'
                    else:
                        # Fallback for string events
                        event_str = str(event).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html += f'            <li>{event_str}</li>\n'
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
        print(f"Found {total_formatted_events} unique events after removing duplicates")
        
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
    print(f"Total events: {total_events}")
    print(f"Months with events: {len(data['events_by_month'])}")