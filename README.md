# ts-media-bridge

A Python package that bridges Spotify and New York Times APIs to analyze the relationship between music streaming popularity and media coverage for Taylor Swift's discography.

**Final Project for Columbia University Modern Data Structures (Fall 2025)**

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Data](#data)
- [Key Findings](#key-findings)
- [Rate Limiting](#rate-limiting)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)


## Overview

`ts-media-bridge` connects artist metadata from Spotify with article coverage from the New York Times to explore how media attention correlates with streaming performance. This package provides tools to:

- Fetch artist and album data from Spotify API
- Search and retrieve articles from NYT Article Search API
- Match articles to specific albums using intelligent text analysis
- Analyze patterns in media coverage vs. streaming popularity
- Handle API rate limiting and pagination automatically

## Features

- **Spotify Integration**: Get comprehensive artist discography with metadata (popularity, release dates, track counts, etc.)
- **NYT Article Search**: Search for articles by artist, album, or custom queries with date filtering
- **Smart Matching**: Automatically match articles to albums using context-aware text analysis
- **Rate Limiting**: Built-in rate limiting to respect API quotas
- **Data Export**: Export results to CSV for further analysis
- **Helper Functions**: Utilities for analyzing tracks by year, comparing re-recordings, and more

## Installation 
### Prerequisites

- Python 3.13+
- API keys (see below)

### Install from source
```bash
# Clone the repository
git clone https://github.com/yourusername/ts-media-bridge.git
cd ts-media-bridge

# Option 1: Install with Poetry
poetry install

# Option 2: Install with pip in development mode
pip install -e .
```

### Install from PyPI (coming soon)
```bash
pip install ts-media-bridge
```

### API Keys Required
You need API keys for both Spotify and NYT:

1. **Spotify API**: Get credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. **NYT API**: Get your key from [NYT Developer Portal](https://developer.nytimes.com/)

Create a `.env` file in the project root:
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
NYT_API_KEY=your_nyt_api_key
```

## Quick Start

```python
from ts_media_bridge import SpotifyClient, NYTClient, match_articles_to_albums

# Initialize clients
sp = SpotifyClient()
nyt = NYTClient()

# Get Taylor Swift's albums from Spotify
taylor_swift_id = "06HL4z0CvFAxyc27GXpf02"
df_albums = sp.get_artist_albums_df(taylor_swift_id)

# Search NYT for articles about Taylor Swift
articles = nyt.search_taylor_swift(pages=5)
df_articles = nyt.docs_to_df(articles)

# Match articles to specific albums
df_matched = match_articles_to_albums(df_albums, df_articles)

# Analyze coverage
mentions = df_matched.groupby("album_base_title")["web_url"].nunique()
print(mentions)
```

## Usage Examples

### Get Artist Albums
```python
from ts_media_bridge import SpotifyClient

sp = SpotifyClient()
df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
print(df_albums[['name', 'release_date', 'popularity']])
```

### Search NYT Articles by Date Range
```python
from ts_media_bridge import NYTClient

nyt = NYTClient()
docs = nyt.search_articles(
    query="Taylor Swift",
    pages=3,
    begin_date="20200101",
    end_date="20221231"
)
df_articles = nyt.docs_to_df(docs)
```

### Compare Original Albums vs Taylor's Versions
```python
from ts_media_bridge import compare_rerecordings

# Assuming you have track-level data
df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
comparison = compare_rerecordings(df_tracks)
print(comparison)
```

## Data

This package includes sample datasets in CSV format:

- **`ts_albums.csv`**: Canonical list of Taylor Swift albums with Spotify metadata
- **`taylor_swift_combined_analysis.csv`**: Combined Spotify + NYT coverage data
- **`album_article_matches.csv`**: Individual article-album matches (60 pairs)
- **`nyt_articles.csv`**: Raw NYT articles collected (126 articles)

## Project Structure

```
ts-media-bridge/
├── ts_media_bridge/
│   ├── __init__.py
│   ├── spotify_client.py      # Spotify API client
│   ├── nyt_client.py           # NYT API client
│   ├── media_bridge.py         # Article-album matching logic
│   ├── spotify_helpers.py      # Analysis helper functions
│   └── utils.py                # Utility functions
├── notebooks/
│   ├── nyt_api_dev.ipynb       # Development notebook
│   └── vignette.ipynb          # Usage examples and analysis
├── tests/
│   └── test_clients.py         # Unit tests
├── pyproject.toml
├── README.md
└── LICENSE
```

## Key Findings

Analysis of 126 NYT articles matched to Taylor Swift's discography revealed:

- **Weak correlation** between Spotify popularity and NYT coverage (r ≈ 0.3)
- **Original albums** receive ~55% more media coverage than re-recordings on average
- **Recency bias**: Newer albums (The Life of a Showgirl, Midnights) dominate coverage
- **Cultural significance** matters more than streaming numbers for NYT coverage
  - Example: *folklore* (75 popularity, 6 mentions) vs *Lover* (88 popularity, 0 mentions)

## Documentation

Full documentation is available at [Read the Docs](https://ts-media-bridge.readthedocs.io) (link to be added).

See the [vignette notebook](notebooks/vignette.ipynb) for detailed usage examples and analysis.

## Rate Limiting

Both APIs have rate limits:

- **Spotify**: Uses client credentials flow, automatic token refresh
- **NYT**: 10 calls per minute, 4000 per day
  - The package automatically waits 6.5 seconds between requests

## Troubleshooting
### Common Issues
**"Missing Spotify credentials" error**
- Make sure your `.env` file is in the project root directory
- Check that `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set correctly
- Verify credentials at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
**NYT Rate Limit (429 error)**
- The package includes automatic rate limiting, but if you interrupt execution you may need to wait
- Wait 60 seconds before retrying if you hit the rate limit
**Import errors after installation**
- Try restarting your Python kernel/interpreter
- Make sure you're in the correct virtual environment

## License

MIT License - see LICENSE file for details

## Author

Sofia Giorgianni (sg3925@columbia.edu)




