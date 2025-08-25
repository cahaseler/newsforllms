# News for LLMs

A tool that extracts and formats significant world events from Wikipedia for LLMs that lack recent training data. Provides a clean, structured summary of major events organized by month.

## Purpose

LLMs typically have training data cutoffs that exclude recent events. This tool provides:
- Key world events from Wikipedia's yearly summary pages
- Clean, LLM-optimized formatting
- Monthly organization for temporal context
- Focus on significant political, economic, and social developments

## Features

- **Wikipedia Scraping**: Extracts events from Wikipedia year pages (e.g., 2025)
- **Smart Filtering**: Prioritizes significant events (elections, policy changes, major incidents)
- **Multiple Formats**: Generates HTML, Markdown, and JSON outputs
- **Clean Text**: Removes citations, edit links, and formatting artifacts
- **Monthly Organization**: Groups events by month for easy navigation
- **Weekly Updates**: GitHub Actions workflow for automatic updates

## Quick Start

### Simple Wikipedia Approach (Recommended)

```bash
# Install minimal dependencies
pip install requests beautifulsoup4 lxml python-dateutil

# Run the Wikipedia scraper
python run_wikipedia.py
```

This generates:
- `output/newsforllms.html` - Main HTML output
- `output/newsforllms_2025.html` - Year-specific HTML
- `output/newsforllms_2025.md` - Markdown version
- `data/processed/wikipedia_2025_events.json` - Structured JSON data

### RSS Feed Approach (Alternative)

For real-time news aggregation from multiple sources:

```bash
# Install full dependencies
pip install -r requirements.txt

# Set up OpenAI API key (optional, for summarization)
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the RSS pipeline
python run_pipeline.py
```

## GitHub Actions Setup

To enable automatic weekly updates:

1. Go to your repository Settings → Secrets and variables → Actions
2. Add a new secret named `OPENAI_API_KEY` with your OpenAI API key
3. The workflow will run automatically every Sunday at 2 AM UTC
4. You can also trigger it manually from the Actions tab

## Project Structure

```
newsforllms/
├── config.py              # Configuration and settings
├── news_aggregator.py     # RSS feed fetcher
├── news_processor.py      # Categorization and summarization
├── html_generator.py      # Static HTML generation
├── run_pipeline.py        # Main pipeline script
├── data/                  # Storage for articles
│   ├── raw/              # Raw RSS feed data
│   └── processed/        # Processed and summarized articles
└── output/               # Generated HTML output
    └── newsforllms.html  # Final output file
```

## How It Works

1. **Aggregation**: Fetches RSS feeds from major news sources
2. **Deduplication**: Removes duplicate stories across sources
3. **Categorization**: Tags articles with relevant topics
4. **Summarization**: Uses GPT-3.5 to create concise 2-3 sentence summaries
5. **Organization**: Groups by month and sorts by date
6. **Generation**: Creates a simple, clean HTML page optimized for LLM reading

## Output Format

The generated HTML page includes:
- Table of contents by month
- Each article with:
  - Publication date
  - Title and summary
  - Topic tags
  - Source citation with link
- Metadata about coverage and last update

## Customization

Edit `config.py` to:
- Add/remove news sources
- Adjust categories
- Change token limits
- Modify output paths

## License

MIT