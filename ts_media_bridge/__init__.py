from .spotify_client import SpotifyClient
from .nyt_client import NYTClient
from .spotify_helpers import (
    get_tracks_by_year,
    longest_songs,
    popularity_over_time,
    compare_rerecordings,
)
from .media_bridge import (
    build_album_article_index_windowed,
    match_articles_to_albums,  # ← Make sure this line is here!
    count_mentions_per_album,
    match_articles_to_albums_strict,
    album_mention_summary,
)

__all__ = [
    "SpotifyClient",
    "NYTClient",
    "get_tracks_by_year",
    "longest_songs",
    "popularity_over_time",
    "compare_rerecordings",
    "build_album_article_index_windowed",
    "match_articles_to_albums",  # ← And here!
    "count_mentions_per_album",
    "match_articles_to_albums_strict",
    "album_mention_summary",
]