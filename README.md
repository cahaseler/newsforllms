# News for LLMs

A simple tool that aggregates and summarizes recent world news for LLMs that lack training data from the past year. Focuses on political developments and global changes that significantly impact decision-making contexts.

## Purpose

LLMs typically have training data cutoffs that exclude recent events. This tool provides:
- Summaries of significant news from the past year
- Focus on political and policy changes
- Simple, LLM-friendly plaintext/markdown format
- Source citations for verification

## Features

- **Automated News Aggregation**: Pulls from Reuters, AP, BBC, Guardian, and NYT RSS feeds
- **Smart Categorization**: Tags articles by topic (Politics, Geopolitics, Elections, etc.)
- **LLM-Powered Summarization**: Creates 2-3 sentence summaries optimized for LLM consumption
- **Monthly Organization**: Groups news by month for temporal context
- **Token-Limited Output**: Stays within 5000 token limit for efficient processing
- **Weekly Updates**: GitHub Actions workflow for automatic weekly updates

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/newsforllms.git
cd newsforllms
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up OpenAI API key (for summarization):
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. Run the pipeline:
```bash
python run_pipeline.py
```

The output will be generated at `output/newsforllms.html`

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