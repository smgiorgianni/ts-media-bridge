"""
Unit tests for ts-media-bridge package.

Run with: pytest tests/test_clients.py -v
Or: pytest tests/ -v (to run all tests)
"""

import pytest
import pandas as pd


class TestSpotifyClient:
    """Tests for SpotifyClient."""

    def test_import(self):
        """Test that SpotifyClient can be imported."""
        from ts_media_bridge import SpotifyClient
        assert SpotifyClient is not None

    def test_initialization(self):
        """Test SpotifyClient initialization."""
        from ts_media_bridge import SpotifyClient
        sp = SpotifyClient()
        assert sp is not None
        assert sp.client_id is not None
        assert sp.client_secret is not None

    def test_get_artist(self):
        """Test getting artist information."""
        from ts_media_bridge import SpotifyClient
        sp = SpotifyClient()
        artist = sp.get_artist("06HL4z0CvFAxyc27GXpf02")  # Taylor Swift
        
        assert artist is not None
        assert artist['name'] == 'Taylor Swift'
        assert 'popularity' in artist
        assert 'followers' in artist

    def test_get_artist_albums_df(self):
        """Test getting albums as DataFrame."""
        from ts_media_bridge import SpotifyClient
        sp = SpotifyClient()
        df = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'name' in df.columns
        assert 'base_title' in df.columns
        assert 'is_rerecording' in df.columns
        assert 'is_deluxe' in df.columns
        assert 'popularity' in df.columns

    def test_get_artist_tracks_df(self):
        """Test getting tracks as DataFrame."""
        from ts_media_bridge import SpotifyClient
        sp = SpotifyClient()
        df = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'track_name' in df.columns
        assert 'album_name' in df.columns
        assert 'duration_ms' in df.columns


class TestNYTClient:
    """Tests for NYTClient."""

    def test_import(self):
        """Test that NYTClient can be imported."""
        from ts_media_bridge import NYTClient
        assert NYTClient is not None

    def test_initialization(self):
        """Test NYTClient initialization."""
        from ts_media_bridge import NYTClient
        nyt = NYTClient()
        assert nyt is not None
        assert nyt.api_key is not None

    def test_search_taylor_swift(self):
        """Test searching for Taylor Swift articles."""
        from ts_media_bridge import NYTClient
        nyt = NYTClient()
        
        # Only fetch 1 page to be quick
        docs = nyt.search_taylor_swift(pages=1)
        
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert 'headline' in docs[0]
        assert 'pub_date' in docs[0]

    def test_docs_to_df(self):
        """Test converting docs to DataFrame."""
        from ts_media_bridge import NYTClient
        nyt = NYTClient()
        
        docs = nyt.search_taylor_swift(pages=1)
        df = nyt.docs_to_df(docs)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'headline' in df.columns
        assert 'pub_date' in df.columns
        assert 'snippet' in df.columns
        assert 'web_url' in df.columns


class TestMediaBridge:
    """Tests for media bridge matching functions."""

    def test_import(self):
        """Test that matching functions can be imported."""
        from ts_media_bridge import match_articles_to_albums
        assert match_articles_to_albums is not None

    def test_match_articles_to_albums(self):
        """Test matching articles to albums."""
        from ts_media_bridge import (
            SpotifyClient,
            NYTClient,
            match_articles_to_albums
        )
        
        sp = SpotifyClient()
        nyt = NYTClient()
        
        df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
        docs = nyt.search_taylor_swift(pages=1)
        df_articles = nyt.docs_to_df(docs)
        
        df_matched = match_articles_to_albums(df_albums, df_articles)
        
        assert isinstance(df_matched, pd.DataFrame)
        # May be empty if no matches found
        if len(df_matched) > 0:
            assert 'album_base_title' in df_matched.columns
            assert 'headline' in df_matched.columns
            assert 'web_url' in df_matched.columns


class TestSpotifyHelpers:
    """Tests for Spotify helper functions."""

    @pytest.fixture
    def tracks_df(self):
        """Fixture to get tracks DataFrame."""
        from ts_media_bridge import SpotifyClient
        sp = SpotifyClient()
        return sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")

    def test_get_tracks_by_year(self, tracks_df):
        """Test filtering tracks by year."""
        from ts_media_bridge import get_tracks_by_year
        
        if len(tracks_df) > 0:
            year = int(tracks_df['album_release_date'].str[:4].iloc[0])
            result = get_tracks_by_year(tracks_df, year)
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0

    def test_longest_songs(self, tracks_df):
        """Test finding longest songs."""
        from ts_media_bridge import longest_songs
        
        result = longest_songs(tracks_df, n=5)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= 5
        if len(result) > 0:
            assert 'duration_min' in result.columns

    def test_popularity_over_time(self, tracks_df):
        """Test popularity over time analysis."""
        from ts_media_bridge import popularity_over_time
        
        result = popularity_over_time(tracks_df)
        
        assert isinstance(result, pd.DataFrame)
        assert 'year' in result.columns
        assert 'avg_album_popularity' in result.columns

    def test_compare_rerecordings(self, tracks_df):
        """Test comparing re-recordings."""
        from ts_media_bridge import compare_rerecordings
        
        result = compare_rerecordings(tracks_df)
        
        assert isinstance(result, pd.DataFrame)
        assert 'album_base_title' in result.columns
