# ts-media-bridge

Bridge Spotify and NYT APIs to analyze the relationship between streaming popularity and media coverage.

## Overview

**ts-media-bridge** is a Python package that connects two data sources—Spotify's music streaming data and The New York Times' article archive—to explore how an artist's commercial success relates to their cultural impact.

This package provides:
- **SpotifyClient**: Easy-to-use wrapper for Spotify's Web API with authentication handling
- **NYTClient**: Interface to The New York Times Article Search API
- **Intelligent text matching**: Automatically connects articles to albums using context-aware algorithms
- **Analysis tools**: Helper functions for exploring trends and patterns in the data

### Key Features

-  **Spotify API Integration**: Fetch artist data, albums, and tracks with automatic OAuth handling
-  **NYT API Integration**: Search and retrieve articles with flexible filtering
-  **Smart Matching**: Connect articles to albums using intelligent text analysis
-  **Analysis Helpers**: Built-in functions for temporal analysis and comparisons
-  **Data Export**: Clean pandas DataFrames ready for visualization and further analysis

## Installation

### Prerequisites

- Python 3.12 or higher
- API credentials:
  - [Spotify Developer Account](https://developer.spotify.com/)
  - [New York Times Developer Account](https://developer.nytimes.com/)

### Install from GitHub
```bash
pip install git+https://github.com/smgiorgianni/ts-media-bridge.git
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/smgiorgianni/ts-media-bridge.git
cd ts-media-bridge

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

## Quick Start

### 1. Set Up API Credentials

Create a `.env` file in your project directory:
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
NYT_API_KEY=your_nyt_api_key
```

### 2. Basic Usage
```python
from ts_media_bridge import SpotifyClient, NYTClient, match_articles_to_albums

# Initialize clients
sp = SpotifyClient()
nyt = NYTClient()

# Get Taylor Swift's albums from Spotify
artist_id = "06HL4z0CvFAxyc27GXpf02"  # Taylor Swift
df_albums = sp.get_artist_albums_df(artist_id)

# Search for Taylor Swift articles in NYT
articles = nyt.search_taylor_swift(pages=5)
df_articles = nyt.docs_to_df(articles)

# Match articles to albums
df_matched = match_articles_to_albums(df_albums, df_articles)

# Analyze results
print(f"Found {len(df_matched)} article-album matches")
coverage = df_matched.groupby('album_base_title')['web_url'].nunique()
print(coverage.sort_values(ascending=False))
```

### 3. Analysis Example
```python
from ts_media_bridge import SpotifyClient, popularity_over_time

sp = SpotifyClient()

# Get all tracks for an artist
tracks_df = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")

# Analyze popularity trends over time
yearly_popularity = popularity_over_time(tracks_df)
print(yearly_popularity)
```

## Documentation

Full documentation is available at: **https://ts-media-bridge.readthedocs.io**

### Key Documentation Pages:

- [Installation Guide](https://ts-media-bridge.readthedocs.io/en/latest/installation.html)
- [Quick Start Tutorial](https://ts-media-bridge.readthedocs.io/en/latest/quickstart.html)
- [API Reference](https://ts-media-bridge.readthedocs.io/en/latest/api.html)
- [Usage Examples](https://ts-media-bridge.readthedocs.io/en/latest/examples.html)

# Key Findings

Analysis of Taylor Swift's discography revealed interesting patterns in the relationship between streaming popularity and media coverage:

**Dataset Summary:**
- 12 albums analyzed
- 7 albums with NYT coverage
- 41 total article-album matches

### 1. Weak Correlation Between Popularity and Coverage

Spotify popularity scores show **weak correlation** with NYT article mentions. High streaming numbers don't guarantee media attention.

**Examples:**
- *Lover* (88 popularity) → 0 NYT mentions
- *Midnights* (82 popularity) → 0 NYT mentions
- *folklore* (75 popularity) → 6 NYT mentions

**Insight:** Cultural significance matters more than commercial metrics.

### 2. Recency Bias Dominates

Recent albums receive disproportionate coverage regardless of popularity scores:

- *The Life of a Showgirl* (2025): **12 mentions** (100 popularity)
- *reputation* (2017): **10 mentions** (87 popularity)
- *folklore* (2020): **6 mentions** (75 popularity)

Meanwhile, classic albums with high popularity get minimal coverage:
- *Taylor Swift* (2006): 0 mentions (67 popularity)
- *1989* (2023, Taylor's Version): 1 mention (82 popularity)

### 3. Original Albums vs Re-recordings

Taylor's Versions receive less coverage than original releases:

**Re-recordings:**
- *Fearless (Taylor's Version)*: 4 mentions
- *Red (Taylor's Version)*: 5 mentions
- *Speak Now (Taylor's Version)*: 0 mentions
- *1989 (Taylor's Version)*: 1 mention

**Originals:**
- *reputation*: 10 mentions
- *folklore*: 6 mentions
- *evermore*: 3 mentions

**Average:** Original albums receive approximately **2x more coverage** than re-recordings.

### 4. Cultural Moments Matter More Than Streaming

The NYT covers artistic evolution and cultural impact over commercial performance:

- *folklore* (pandemic-era surprise album): 6 mentions despite lower popularity (75)
- *reputation* (post-controversy comeback): 10 mentions
- *The Life of a Showgirl* (new release): 12 mentions

High-popularity albums without cultural narratives get overlooked:
- *Lover*: 88 popularity, 0 mentions
- *THE TORTURED POETS DEPARTMENT*: 82 popularity, 0 mentions

## API Clients

### SpotifyClient

Handles Spotify Web API authentication and data retrieval:
```python
from ts_media_bridge import SpotifyClient

sp = SpotifyClient()

# Get artist information
artist = sp.get_artist("06HL4z0CvFAxyc27GXpf02")
print(f"{artist['name']}: {artist['followers']['total']:,} followers")

# Get albums as DataFrame
df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
print(df_albums[['name', 'release_date', 'popularity']].head())

# Get all tracks
df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
```

**Key Methods:**
- `get_artist()` - Fetch artist metadata
- `get_artist_albums_df()` - Get albums with smart filtering (removes duplicates, adds flags)
- `get_artist_tracks_df()` - Get all tracks across all albums
- `get_album_tracks()` - Get tracks from a specific album

### NYTClient

Interfaces with The New York Times Article Search API:
```python
from ts_media_bridge import NYTClient

nyt = NYTClient()

# Search for articles
articles = nyt.search_articles("Taylor Swift", pages=3)
print(f"Found {len(articles)} articles")

# Search with date filters
recent = nyt.search_taylor_swift(pages=5, begin_date="20230101")

# Convert to DataFrame
df_articles = nyt.docs_to_df(articles)
print(df_articles[['headline', 'pub_date', 'section_name']].head())
```

**Key Methods:**
- `search_articles()` - General article search
- `search_taylor_swift()` - Convenience wrapper for Taylor Swift articles
- `docs_to_df()` - Convert articles to pandas DataFrame

## Helper Functions

### Matching
```python
from ts_media_bridge import match_articles_to_albums

# Match articles to albums
df_matched = match_articles_to_albums(df_albums, df_articles)
```

### Analysis Tools
```python
from ts_media_bridge import (
    get_tracks_by_year,
    longest_songs,
    popularity_over_time,
    compare_rerecordings
)

# Get tracks from a specific year
tracks_2020 = get_tracks_by_year(df_tracks, 2020)

# Find longest songs
top_10_longest = longest_songs(df_tracks, n=10)

# Analyze popularity trends
yearly_trends = popularity_over_time(df_tracks)

# Compare originals vs re-recordings
comparison = compare_rerecordings(df_albums)
```

## Examples

### Example 1: Album Coverage Analysis
```python
from ts_media_bridge import SpotifyClient, NYTClient, match_articles_to_albums

# Initialize
sp = SpotifyClient()
nyt = NYTClient()

# Get data
df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
articles = nyt.search_taylor_swift(pages=10)
df_articles = nyt.docs_to_df(articles)

# Match and analyze
df_matched = match_articles_to_albums(df_albums, df_articles)

# Count mentions per album
mentions = (
    df_matched.groupby('album_base_title')['web_url']
    .nunique()
    .sort_values(ascending=False)
)
print(mentions)
```

### Example 2: Temporal Analysis
```python
from ts_media_bridge import SpotifyClient, popularity_over_time

sp = SpotifyClient()
df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")

# Analyze how popularity changes over release years
yearly_avg = popularity_over_time(df_tracks)
print(yearly_avg)
```

### Example 3: Re-recording Comparison
```python
from ts_media_bridge import SpotifyClient, compare_rerecordings

sp = SpotifyClient()
df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")

# Compare originals vs Taylor's Versions
comparison = compare_rerecordings(df_albums)
print(comparison)
```

## Development

### Running Tests
```bash
# Run smoke tests
python tests/test_basic.py

# Run with pytest
pytest tests/ -v
```

### Building Documentation
```bash
cd docs
make html
```

Documentation will be generated in `docs/build/html/`.

### Contributing

## Requirements

- Python >= 3.12
- requests >= 2.31.0
- pandas >= 2.0.0
- python-dotenv >= 1.0.0

For documentation:
- sphinx >= 8.0.0
- sphinx-rtd-theme >= 3.0.0
- sphinx-autodoc-typehints >= 2.0.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Sofia Giorgianni**  
Columbia University, Fall 2025  
[sg3925@columbia.edu](mailto:sg3925@columbia.edu)

## Links

- **Documentation**: https://ts-media-bridge.readthedocs.io
- **GitHub**: https://github.com/smgiorgianni/ts-media-bridge
- **PyPI**: https://test.pypi.org/project/ts-media-bridge/

---

*Note: This package requires valid API credentials from both Spotify and The New York Times. Please ensure you comply with their respective Terms of Service when using this package.*
