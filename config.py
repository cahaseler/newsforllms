import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# News Sources - RSS feeds for reliable global news
NEWS_SOURCES = {
    "reuters": {
        "world": "https://feeds.reuters.com/reuters/worldNews",
        "politics": "https://feeds.reuters.com/reuters/politicsNews",
        "top": "https://feeds.reuters.com/reuters/topNews"
    },
    "ap": {
        "world": "https://feeds.apnews.com/rss/apf-worldnews",
        "politics": "https://feeds.apnews.com/rss/apf-politics",
        "top": "https://feeds.apnews.com/rss/apf-topnews"
    },
    "bbc": {
        "world": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "politics": "http://feeds.bbci.co.uk/news/politics/rss.xml"
    },
    "guardian": {
        "world": "https://www.theguardian.com/world/rss",
        "politics": "https://www.theguardian.com/politics/rss"
    },
    "nyt": {
        "world": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "politics": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
    }
}

# Categories for tagging
CATEGORIES = [
    "Politics",
    "Geopolitics",
    "Elections",
    "Policy Changes",
    "International Relations",
    "Economic Policy",
    "Climate & Environment",
    "Technology & AI",
    "Military & Defense",
    "Social Movements",
    "Legal & Courts",
    "Public Health"
]

# Output settings
MAX_OUTPUT_TOKENS = 5000
SUMMARY_LENGTH = 100  # Approximate words per summary (2-3 sentences)
OUTPUT_FILE = OUTPUT_DIR / "newsforllms.html"
DATABASE_FILE = PROCESSED_DATA_DIR / "news_database.json"