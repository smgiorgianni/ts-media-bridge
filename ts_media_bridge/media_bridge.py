"""
Media Bridge Module

Functions for matching NYT articles to Spotify albums and analyzing coverage patterns.

This module provides intelligent text matching that handles:
- Generic album titles (Red, Lover, etc.) that need music context to disambiguate
- Distinctive titles (The Life of a Showgirl, etc.) that can be matched directly
- Taylor's Versions vs original albums
- Time-windowed searches based on album release dates

Key Functions
-------------
- match_articles_to_albums: Match articles to albums using smart text analysis
- build_album_article_index_windowed: Search NYT by album with date windows
- count_mentions_per_album: Summarize coverage per album
- album_mention_summary: High-level workflow combining Spotify + NYT data
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .nyt_client import NYTClient

# -------------------------------------------------------------------
# Canonical release dates for Taylor Swift albums
# -------------------------------------------------------------------

TS_ALBUM_RELEASE_DATES = {
    "Taylor Swift": "2006-10-24",
    "Fearless": "2008-11-11",
    "Speak Now": "2010-10-25",
    "Red": "2012-10-22",
    "1989": "2014-10-27",
    "reputation": "2017-11-10",
    "Lover": "2019-08-23",
    "folklore": "2020-07-24",
    "evermore": "2020-12-11",
    "Midnights": "2022-10-21",
    "THE TORTURED POETS DEPARTMENT": "2024-04-19",
    "The Life of a Showgirl": "2025-10-03",
    "Fearless (Taylor's Version)": "2021-04-09",
    "Red (Taylor's Version)": "2021-11-12",
    "Speak Now (Taylor's Version)": "2023-07-07",
    "1989 (Taylor's Version)": "2023-10-27",
    "folklore (deluxe version)": "2020-08-18",
    "evermore (deluxe version)": "2021-01-07",
}

# Generic album titles that need context to match properly
GENERIC_TITLES = {
    "red",
    "lover",
    "reputation",
    "midnights",
    "folklore",
    "evermore",
    "taylor swift",
}

# Keywords that indicate music context
MUSIC_CONTEXT_KEYWORDS = [
    "album",
    "record",
    "song",
    "track",
    "lp",
    "ep",
]


def album_to_search_window(release_date: str, years_after: int = 2) -> Tuple[str, str]:
    """
    Convert album release date to NYT API search window.

    Given an album release date, returns a time window covering from the
    release year through N years after release.

    Parameters
    ----------
    release_date : str
        Album release date in YYYY-MM-DD format
    years_after : int, default 2
        Number of years after release to include in window

    Returns
    -------
    tuple of (str, str)
        (begin_date, end_date) in YYYYMMDD format for NYT API

    Examples
    --------
    >>> begin, end = album_to_search_window("2020-07-24", years_after=2)
    >>> print(begin, end)
    '20200101' '20220101'
    """
    dt = datetime.datetime.strptime(release_date, "%Y-%m-%d")
    begin = dt.replace(month=1, day=1)
    end = begin.replace(year=begin.year + years_after)
    return begin.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def build_album_article_index_windowed(
    df_albums: pd.DataFrame,
    nyt_client: NYTClient,
    pages_per_album: int = 1,
    years_after: int = 2,
) -> pd.DataFrame:
    """
    Build NYT article index per album using date-windowed searches.

    For each album, searches NYT within a time window based on the album's
    release date. This focuses searches on the period when coverage is most likely.

    Parameters
    ----------
    df_albums : pandas.DataFrame
        Spotify album DataFrame with 'base_title' column
    nyt_client : NYTClient
        Initialized NYT API client
    pages_per_album : int, default 1
        Number of NYT result pages to fetch per album (10 results per page)
    years_after : int, default 2
        Years after release to include in search window

    Returns
    -------
    pandas.DataFrame
        Articles with 'album_base_title' column indicating matched album

    Examples
    --------
    >>> from ts_media_bridge import SpotifyClient, NYTClient
    >>> sp = SpotifyClient()
    >>> nyt = NYTClient()
    >>> df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
    >>> df_articles = build_album_article_index_windowed(df_albums, nyt, pages_per_album=1)
    """
    all_rows: List[pd.DataFrame] = []

    for _, row in df_albums.iterrows():
        title = row["base_title"]

        release_date = TS_ALBUM_RELEASE_DATES.get(title)
        if not release_date:
            print(f"[NYT] Skipping album with unknown release date: {title}")
            continue

        begin_date, end_date = album_to_search_window(release_date, years_after=years_after)

        print(
            f"\n[NYT] Searching {title!r} "
            f"(release {release_date}) between {begin_date} and {end_date}"
        )

        try:
            docs = nyt_client.search_album(
                album_name=title,
                pages=pages_per_album,
                begin_date=begin_date,
                end_date=end_date,
            )
        except Exception as e:
            print(f"[NYT] Error while searching for {title!r}: {e}")
            continue

        if not docs:
            continue

        df_docs = nyt_client.docs_to_df(docs)
        if df_docs.empty:
            continue

        df_docs["album_base_title"] = title
        all_rows.append(df_docs)

    if not all_rows:
        return pd.DataFrame()

    return pd.concat(all_rows, ignore_index=True)


def _normalize(text: str) -> str:
    """
    Normalize text for matching: lowercase, remove punctuation, collapse whitespace.

    Parameters
    ----------
    text : str
        Text to normalize

    Returns
    -------
    str
        Normalized text
    """
    if text is None:
        return ""
    text = text.lower()
    # keep letters, digits, and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _has_music_context(text_norm: str) -> bool:
    """
    Check if normalized text contains music-related keywords.

    Parameters
    ----------
    text_norm : str
        Normalized text to check

    Returns
    -------
    bool
        True if text contains music context keywords
    """
    return any(kw in text_norm for kw in MUSIC_CONTEXT_KEYWORDS)


def match_articles_to_albums(
    df_albums: pd.DataFrame,
    df_articles: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match NYT articles to Taylor Swift albums using intelligent text matching.

    Uses context-aware matching that handles:
    - Generic titles (Red, Lover) requiring music keywords for disambiguation
    - Distinctive titles (The Life of a Showgirl) matched directly
    - Self-titled album requiring "debut album" or "self-titled" phrases

    Parameters
    ----------
    df_albums : pandas.DataFrame
        Album DataFrame with 'base_title' or 'name' column
    df_articles : pandas.DataFrame
        Articles DataFrame with 'headline' and 'snippet' columns

    Returns
    -------
    pandas.DataFrame
        Matched article-album pairs with columns:
        - album_id, album_name, album_base_title, album_release_date
        - pub_date, headline, snippet, section, source, news_desk
        - type_of_material, web_url, match_in

    Examples
    --------
    >>> df_matched = match_articles_to_albums(df_albums, df_articles)
    >>> mentions = df_matched.groupby("album_base_title")["web_url"].nunique()
    >>> print(mentions)
    """
    albums = df_albums.copy()
    articles = df_articles.copy()

    # Decide which text we'll use as the "title key"
    if "base_title" in albums.columns:
        albums["title_key"] = albums["base_title"].fillna(albums["name"])
    else:
        albums["title_key"] = albums["name"]

    albums["title_key_norm"] = albums["title_key"].astype(str).apply(_normalize)
    albums["name_norm"] = albums["name"].astype(str).apply(_normalize)

    # Normalize article texts
    articles["headline_norm"] = articles["headline"].astype(str).apply(_normalize)
    articles["snippet_norm"] = articles["snippet"].astype(str).apply(_normalize)

    matches: List[dict] = []

    for _, alb in albums.iterrows():
        album_id = alb.get("id")
        album_name = alb.get("name")
        album_base_title = alb.get("base_title")
        album_release_date = alb.get("release_date")

        base_norm = alb.get("title_key_norm", "")
        full_norm = alb.get("name_norm", "")

        if not full_norm and not base_norm:
            continue

        is_generic = base_norm in GENERIC_TITLES

        # Pre-build regex for word-boundary match on generic titles
        generic_pattern = None
        if is_generic and base_norm:
            generic_pattern = re.compile(rf"\b{re.escape(base_norm)}\b")

        for _, art in articles.iterrows():
            h = art.get("headline_norm", "") or ""
            s = art.get("snippet_norm", "") or ""

            if is_generic:
                # For generic titles, require word-boundary match + music context
                in_headline = False
                in_snippet = False

                if generic_pattern:
                    if generic_pattern.search(h) and _has_music_context(h):
                        in_headline = True
                    if generic_pattern.search(s) and _has_music_context(s):
                        in_snippet = True

                # Special case: self-titled "Taylor Swift" album
                if base_norm == "taylor swift":

                    def has_album_context(text_norm: str) -> bool:
                        return (
                            "debut album" in text_norm
                            or "self titled" in text_norm
                            or "selftitled" in text_norm
                        )

                    if in_headline:
                        in_headline = has_album_context(h)
                    if in_snippet:
                        in_snippet = has_album_context(s)

            else:
                # Distinctive album titles can safely match on base title substring
                in_headline = base_norm in h if base_norm else False
                in_snippet = base_norm in s if base_norm else False

            if not (in_headline or in_snippet):
                continue

            if in_headline and in_snippet:
                match_in = "both"
            elif in_headline:
                match_in = "headline"
            else:
                match_in = "snippet"

            matches.append(
                {
                    "album_id": album_id,
                    "album_name": album_name,
                    "album_base_title": album_base_title,
                    "album_release_date": album_release_date,
                    "pub_date": art.get("pub_date"),
                    "headline": art.get("headline"),
                    "snippet": art.get("snippet"),
                    "section": art.get("section"),
                    "source": art.get("source"),
                    "news_desk": art.get("news_desk"),
                    "type_of_material": art.get("type_of_material"),
                    "web_url": art.get("web_url"),
                    "match_in": match_in,
                }
            )

    if not matches:
        return pd.DataFrame()

    return pd.DataFrame(matches)


def count_mentions_per_album(
    df_album_articles: pd.DataFrame,
    unique_by_url: bool = True,
) -> pd.DataFrame:
    """
    Summarize NYT article mentions by album.

    Parameters
    ----------
    df_album_articles : pandas.DataFrame
        DataFrame with 'album_base_title' and 'web_url' columns
    unique_by_url : bool, default True
        If True, count unique URLs (avoids double-counting same article)

    Returns
    -------
    pandas.DataFrame
        Summary with columns: album_base_title, mention_count

    Examples
    --------
    >>> mentions = count_mentions_per_album(df_matched)
    >>> print(mentions.head())
    """
    if df_album_articles is None or df_album_articles.empty:
        return pd.DataFrame(columns=["album_base_title", "mention_count"])

    if unique_by_url and "web_url" in df_album_articles.columns:
        grouped = (
            df_album_articles.groupby("album_base_title")["web_url"]
            .nunique()
            .reset_index(name="mention_count")
        )
    else:
        grouped = (
            df_album_articles.groupby("album_base_title").size().reset_index(name="mention_count")
        )

    return grouped.sort_values("mention_count", ascending=False).reset_index(drop=True)


def match_articles_to_albums_strict(
    df_articles: pd.DataFrame,
    df_albums: pd.DataFrame,
    skip_ambiguous: bool = True,
) -> pd.DataFrame:
    """
    Strictly match NYT articles to albums using word-boundary matching.

    Unlike match_articles_to_albums(), this uses simple word-boundary regex
    without context analysis. Useful for validation or comparison.

    Parameters
    ----------
    df_articles : pandas.DataFrame
        Articles with 'headline' and 'snippet' columns
    df_albums : pandas.DataFrame
        Albums with 'base_title' column
    skip_ambiguous : bool, default True
        If True, skip self-titled "Taylor Swift" album

    Returns
    -------
    pandas.DataFrame
        Matched pairs with columns: album_base_title, pub_date, headline, snippet, web_url
    """
    rows = []

    titles = df_albums["base_title"].dropna().unique().tolist()
    if skip_ambiguous:
        titles = [t for t in titles if t.lower() != "taylor swift"]

    for _, art in df_articles.iterrows():
        text = f"{art.get('headline', '')} {art.get('snippet', '')}".lower()

        for title in titles:
            pattern = r"\b" + re.escape(title.lower()) + r"\b"
            if re.search(pattern, text):
                rows.append(
                    {
                        "album_base_title": title,
                        "pub_date": art.get("pub_date"),
                        "headline": art.get("headline"),
                        "snippet": art.get("snippet"),
                        "web_url": art.get("web_url"),
                    }
                )

    return pd.DataFrame(rows)


def album_mention_summary(
    spotify_client,
    nyt_client: NYTClient,
    artist_id: str,
    pages: int = 3,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    High-level workflow: get albums, search NYT, match, and summarize.

    Combines Spotify album data with NYT article searches to produce
    a summary of media coverage per album.

    Parameters
    ----------
    spotify_client : SpotifyClient
        Initialized Spotify API client
    nyt_client : NYTClient
        Initialized NYT API client
    artist_id : str
        Spotify artist ID
    pages : int, default 3
        Number of NYT pages to search

    Returns
    -------
    tuple of (pandas.DataFrame, pandas.DataFrame)
        - df_matches: Individual article-album matches
        - mentions_per_album: Summary of mentions per album

    Examples
    --------
    >>> from ts_media_bridge import SpotifyClient, NYTClient
    >>> sp = SpotifyClient()
    >>> nyt = NYTClient()
    >>> matches, summary = album_mention_summary(sp, nyt, "06HL4z0CvFAxyc27GXpf02", pages=5)
    >>> print(summary)
    """
    # Get albums (includes base_title, rerecording flags, etc.)
    df_albums = spotify_client.get_artist_albums_df(artist_id)

    # Get corpus of Taylor Swift coverage from NYT
    docs = nyt_client.search_taylor_swift(pages=pages)
    df_articles = nyt_client.docs_to_df(docs)

    # Strict album/title matching
    df_matches = match_articles_to_albums_strict(df_articles, df_albums)

    mentions_per_album = (
        df_matches.groupby("album_base_title")["web_url"]
        .nunique()
        .reset_index(name="nyt_article_count")
        .sort_values("nyt_article_count", ascending=False)
    )

    return df_matches, mentions_per_album