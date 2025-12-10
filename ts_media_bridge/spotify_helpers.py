"""
Spotify Helper Functions

Utility functions for analyzing Taylor Swift's discography data from Spotify.

These functions operate on track-level DataFrames returned by
SpotifyClient.get_artist_tracks_df() to provide various analyses.

Functions
---------
- get_tracks_by_year: Filter tracks by release year
- longest_songs: Find the longest tracks
- popularity_over_time: Analyze popularity trends over time
- compare_rerecordings: Compare originals vs Taylor's Versions

Examples
--------
>>> from ts_media_bridge import SpotifyClient, get_tracks_by_year, longest_songs
>>> sp = SpotifyClient()
>>> df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
>>> tracks_2020 = get_tracks_by_year(df_tracks, 2020)
>>> long_tracks = longest_songs(df_tracks, n=10)
"""

import pandas as pd


def get_tracks_by_year(df_tracks: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Filter tracks by album release year.

    Parameters
    ----------
    df_tracks : pandas.DataFrame
        Track DataFrame with 'album_release_date' column
    year : int
        Year to filter by (e.g., 2020)

    Returns
    -------
    pandas.DataFrame
        Tracks released in the specified year

    Raises
    ------
    ValueError
        If 'album_release_date' column is missing

    Examples
    --------
    >>> tracks_2020 = get_tracks_by_year(df_tracks, 2020)
    >>> print(f"Tracks from 2020: {len(tracks_2020)}")
    """
    df = df_tracks.copy()

    if "album_release_date" not in df.columns:
        raise ValueError("df_tracks must contain album_release_date column.")

    df["year"] = df["album_release_date"].astype(str).str[:4].astype(int)

    return df[df["year"] == year].reset_index(drop=True)


def longest_songs(df_tracks: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return the N longest Taylor Swift songs.

    Parameters
    ----------
    df_tracks : pandas.DataFrame
        Track DataFrame with 'duration_ms' column
    n : int, default 10
        Number of longest tracks to return

    Returns
    -------
    pandas.DataFrame
        Top N longest tracks with 'duration_min' column added

    Raises
    ------
    ValueError
        If 'duration_ms' column is missing

    Examples
    --------
    >>> longest = longest_songs(df_tracks, n=5)
    >>> print(longest[['track_name', 'duration_min']])
    """
    df = df_tracks.copy()

    if "duration_ms" not in df.columns:
        raise ValueError("df_tracks must contain duration_ms column.")

    df["duration_min"] = df["duration_ms"] / 60000

    return df.sort_values("duration_ms", ascending=False).head(n).reset_index(drop=True)


def popularity_over_time(df_tracks: pd.DataFrame) -> pd.DataFrame:
    """
    Compute average album popularity per release year.

    Parameters
    ----------
    df_tracks : pandas.DataFrame
        Track DataFrame with 'album_popularity' and 'album_release_date' columns

    Returns
    -------
    pandas.DataFrame
        Summary with columns: year, avg_album_popularity

    Raises
    ------
    ValueError
        If 'album_popularity' column is missing

    Examples
    --------
    >>> summary = popularity_over_time(df_tracks)
    >>> print(summary)
    """
    df = df_tracks.copy()

    if "album_popularity" not in df.columns:
        raise ValueError("df_tracks must contain album_popularity column.")

    df["year"] = df["album_release_date"].astype(str).str[:4].astype(int)

    summary = (
        df.groupby("year")["album_popularity"]
        .mean()
        .reset_index()
        .rename(columns={"album_popularity": "avg_album_popularity"})
    )

    return summary.sort_values("year")


def compare_rerecordings(df_tracks: pd.DataFrame) -> pd.DataFrame:
    """
    Compare average popularity between original albums and Taylor's Versions.

    Parameters
    ----------
    df_tracks : pandas.DataFrame
        Track DataFrame with 'album_base_title', 'album_is_rerecording',
        and 'album_popularity' columns

    Returns
    -------
    pandas.DataFrame
        Comparison with columns: album_base_title, original, rerecording
        Values are average popularity scores

    Raises
    ------
    ValueError
        If 'album_base_title' column is missing

    Examples
    --------
    >>> comparison = compare_rerecordings(df_tracks)
    >>> print(comparison)
    """
    df = df_tracks.copy()

    if "album_base_title" not in df.columns:
        raise ValueError("df_tracks must contain album_base_title.")

    base = (
        df.groupby(["album_base_title", "album_is_rerecording"])["album_popularity"]
        .mean()
        .reset_index()
    )

    pivot = base.pivot(
        index="album_base_title", columns="album_is_rerecording", values="album_popularity"
    ).rename(columns={False: "original", True: "rerecording"})

    return pivot.reset_index()