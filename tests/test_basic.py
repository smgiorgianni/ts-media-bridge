"""
Basic smoke tests to verify the package works after changes.

Run with: python test_basic.py
Or with pytest: pytest test_basic.py -v
"""

def test_imports():
    """Test that all modules import without errors."""
    try:
        from ts_media_bridge import (
            SpotifyClient,
            NYTClient,
            match_articles_to_albums,
            get_tracks_by_year,
            longest_songs,
            popularity_over_time,
            compare_rerecordings,
            build_album_article_index_windowed,
        )
        print(" All imports successful")
        return True
    except Exception as e:
        print(f" Import failed: {e}")
        return False


def test_spotify_client():
    """Test SpotifyClient initialization and basic functionality."""
    try:
        from ts_media_bridge import SpotifyClient
        
        sp = SpotifyClient()
        print(" SpotifyClient initialized")
        
        # Test get_artist
        artist = sp.get_artist("06HL4z0CvFAxyc27GXpf02")
        assert artist['name'] == 'Taylor Swift'
        print(f" Got artist: {artist['name']}")
        
        # Test get_artist_albums_df
        df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
        assert len(df_albums) > 0
        assert 'base_title' in df_albums.columns
        assert 'is_rerecording' in df_albums.columns
        print(f" Got {len(df_albums)} albums with proper structure")
        
        return True
    except Exception as e:
        print(f" SpotifyClient test failed: {e}")
        return False


def test_nyt_client():
    """Test NYTClient initialization and basic functionality."""
    try:
        from ts_media_bridge import NYTClient
        
        nyt = NYTClient()
        print(" NYTClient initialized")
        
        # Test search (just 1 page to be quick)
        docs = nyt.search_taylor_swift(pages=1)
        assert len(docs) > 0
        print(f" NYT search returned {len(docs)} articles")
        
        # Test docs_to_df
        df_articles = nyt.docs_to_df(docs)
        assert len(df_articles) > 0
        assert 'headline' in df_articles.columns
        assert 'pub_date' in df_articles.columns
        print(f" Converted to DataFrame with {len(df_articles)} rows")
        
        return True
    except Exception as e:
        print(f" NYTClient test failed: {e}")
        return False


def test_matching():
    """Test article-album matching functionality."""
    try:
        from ts_media_bridge import SpotifyClient, NYTClient, match_articles_to_albums
        
        sp = SpotifyClient()
        nyt = NYTClient()
        
        df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
        docs = nyt.search_taylor_swift(pages=1)
        df_articles = nyt.docs_to_df(docs)
        
        df_matched = match_articles_to_albums(df_albums, df_articles)
        assert 'album_base_title' in df_matched.columns
        assert 'headline' in df_matched.columns
        print(f" Matched {len(df_matched)} article-album pairs")
        
        return True
    except Exception as e:
        print(f" Matching test failed: {e}")
        return False


def test_helper_functions():
    """Test Spotify helper functions."""
    try:
        from ts_media_bridge import SpotifyClient, get_tracks_by_year, longest_songs
        import pandas as pd
        
        sp = SpotifyClient()
        
        # Get tracks (just get a small sample for testing)
        df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
        
        if len(df_tracks) > 0:
            # Test get_tracks_by_year
            year = int(df_tracks['album_release_date'].str[:4].iloc[0])
            tracks_year = get_tracks_by_year(df_tracks, year)
            assert len(tracks_year) > 0
            print(f" get_tracks_by_year works")
            
            # Test longest_songs
            long = longest_songs(df_tracks, n=5)
            assert len(long) <= 5
            print(f" longest_songs works")
        
        return True
    except Exception as e:
        print(f" Helper functions test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Running Basic Smoke Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("SpotifyClient", test_spotify_client),
        ("NYTClient", test_nyt_client),
        ("Matching", test_matching),
        ("Helper Functions", test_helper_functions),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n All tests passed! Your code is working correctly.")
    else:
        print("\n Some tests failed. Check the output above for details.")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
