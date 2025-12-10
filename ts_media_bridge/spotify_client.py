from __future__ import annotations

import base64
import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


TS_CANONICAL_ALBUMS = {
    "Taylor Swift",
    "Fearless",
    "Fearless (Taylor's Version)",
    "Speak Now",
    "Speak Now (Taylor's Version)",
    "Red",
    "Red (Taylor's Version)",
    "1989",
    "1989 (Taylor's Version)",
    "reputation",
    "Lover",
    "folklore",
    "folklore (deluxe version)",
    "evermore",
    "evermore (deluxe version)",
    "Midnights",
    "THE TORTURED POETS DEPARTMENT",
    "The Tortured Poets Department",
    "The Life of a Showgirl",
}


class SpotifyAuthError(RuntimeError):
    """Raised when Spotify authentication fails."""


class SpotifyClient:
    """
    Spotify API client using the Client Credentials flow.

    Handles authentication, token refresh, and provides methods for fetching
    artist, album, and track data from Spotify's Web API.

    Parameters
    ----------
    client_id : str, optional
        Spotify client ID. If not provided, reads from SPOTIFY_CLIENT_ID environment variable.
    client_secret : str, optional
        Spotify client secret. If not provided, reads from SPOTIFY_CLIENT_SECRET environment variable.

    Attributes
    ----------
    client_id : str
        Spotify application client ID
    client_secret : str
        Spotify application client secret

    Examples
    --------
    >>> sp = SpotifyClient()
    >>> artist = sp.get_artist("06HL4z0CvFAxyc27GXpf02")  # Taylor Swift
    >>> print(artist['name'])
    'Taylor Swift'
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        # Load .env so we can read SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET
        load_dotenv()

        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise SpotifyAuthError(
                "Missing Spotify credentials. "
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your environment or .env file."
            )

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0  # unix timestamp

    # ---------- Internal helpers ----------

    def _ensure_token(self) -> str:
        """
        Return a valid access token, refreshing it if necessary.
        """
        now = time.time()
        # Reuse token if still valid (with a small safety margin)
        if self._access_token and now < self._token_expires_at - 30:
            return self._access_token

        # Otherwise, request a new token
        auth_bytes = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=15)
        if not resp.ok:
            raise SpotifyAuthError(
                f"Failed to obtain token: {resp.status_code} {resp.text[:200]}"
            )

        js = resp.json()
        self._access_token = js["access_token"]
        # expires_in is usually 3600 seconds
        self._token_expires_at = now + js.get("expires_in", 3600)
        return self._access_token

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal helper to send a GET request to /v1/... and return JSON.
        """
        token = self._ensure_token()
        url = f"{SPOTIFY_API_BASE}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {token}"}

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ---------- Public API methods ----------

    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """
        Fetch artist metadata for a given Spotify artist ID.

        Parameters
        ----------
        artist_id : str
            Spotify artist ID (e.g., '06HL4z0CvFAxyc27GXpf02' for Taylor Swift)

        Returns
        -------
        dict
            Artist metadata including name, genres, popularity, followers, etc.

        Examples
        --------
        >>> sp = SpotifyClient()
        >>> artist = sp.get_artist('06HL4z0CvFAxyc27GXpf02')
        >>> print(artist['name'], artist['popularity'])
        """
        return self._get(f"artists/{artist_id}")

    def get_artist_albums(
        self,
        artist_id: str,
        include_groups: str = "album,single",
        market: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all albums for an artist, handling pagination automatically.

        Parameters
        ----------
        artist_id : str
            Spotify artist ID
        include_groups : str, default "album,single"
            Comma-separated list of item types to include.
            Options: 'album', 'single', 'appears_on', 'compilation'
        market : str, optional
            ISO 3166-1 alpha-2 country code (e.g., 'US')
        limit : int, default 50
            Number of results per page (max 50)

        Returns
        -------
        list of dict
            List of album objects

        Examples
        --------
        >>> sp = SpotifyClient()
        >>> albums = sp.get_artist_albums('06HL4z0CvFAxyc27GXpf02', include_groups='album')
        >>> print(f"Found {len(albums)} albums")
        """
        albums: List[Dict[str, Any]] = []
        params: Dict[str, Any] = {
            "include_groups": include_groups,
            "limit": limit,
        }
        if market:
            params["market"] = market

        url_path = f"artists/{artist_id}/albums"

        while True:
            page = self._get(url_path, params=params)
            items = page.get("items", [])
            albums.extend(items)

            next_url = page.get("next")
            if not next_url:
                break

            # Spotify gives a full URL for `next`; parse the query params for the next call
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(next_url)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            # The path will look like '/v1/artists/{id}/albums'
            url_path = parsed.path.replace("/v1/", "")

        return albums

    def get_album(self, album_id: str) -> Dict[str, Any]:
        """
        Fetch full metadata for a single album by ID.

        Parameters
        ----------
        album_id : str
            Spotify album ID

        Returns
        -------
        dict
            Album metadata including tracks, popularity, label, etc.
        """
        return self._get(f"albums/{album_id}")

    def get_album_tracks(
        self,
        album_id: str,
        limit: int = 50,
        market: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all tracks for a given album, handling pagination.

        Parameters
        ----------
        album_id : str
            Spotify album ID
        limit : int, default 50
            Number of results per page (max 50)
        market : str, optional
            ISO 3166-1 alpha-2 country code

        Returns
        -------
        list of dict
            List of track objects
        """
        tracks: List[Dict[str, Any]] = []
        params: Dict[str, Any] = {"limit": limit}
        if market:
            params["market"] = market

        path = f"albums/{album_id}/tracks"

        while True:
            page = self._get(path, params=params)
            items = page.get("items", [])
            tracks.extend(items)

            next_url = page.get("next")
            if not next_url:
                break

            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(next_url)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            path = parsed.path.replace("/v1/", "")

        return tracks

    def get_album_details(self, album_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed album metadata for multiple albums.

        Parameters
        ----------
        album_ids : list of str
            List of Spotify album IDs

        Returns
        -------
        list of dict
            List of album objects with full metadata
        """
        details: List[Dict[str, Any]] = []
        for album_id in album_ids:
            try:
                details.append(self.get_album(album_id))
            except Exception as e:
                print(f"[warning] Error fetching album {album_id}: {e}")
                continue
        return details

    def get_artist_albums_df(
        self,
        artist_id: str,
        include_groups: str = "album,single",
        market: Optional[str] = None,
        primary_artist_only: bool = True,
    ) -> "pd.DataFrame":
        """
        Get artist's albums as a pandas DataFrame with enriched metadata.

        Fetches albums, filters to canonical Taylor Swift albums, and adds
        metadata like popularity, label, and flags for re-recordings and deluxe editions.

        Parameters
        ----------
        artist_id : str
            Spotify artist ID
        include_groups : str, default "album,single"
            Album types to include
        market : str, optional
            ISO 3166-1 alpha-2 country code
        primary_artist_only : bool, default True
            If True, only include albums where artist is primary artist

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns: id, name, base_title, album_type, total_tracks,
            release_date, popularity, label, is_rerecording, is_deluxe, etc.

        Examples
        --------
        >>> sp = SpotifyClient()
        >>> df = sp.get_artist_albums_df('06HL4z0CvFAxyc27GXpf02')
        >>> print(df[['name', 'release_date', 'popularity']])
        """
        import pandas as pd

        # 1) Get basic albums
        albums = self.get_artist_albums(
            artist_id=artist_id,
            include_groups=include_groups,
            market=market,
        )
        if not albums:
            return pd.DataFrame()

        df_basic = pd.json_normalize(albums)

        # 2) Filter to primary-artist albums
        if primary_artist_only and "artists" in df_basic.columns:

            def _is_primary_artist(artists_list):
                if not isinstance(artists_list, list) or not artists_list:
                    return False
                return artists_list[0].get("id") == artist_id

            df_basic = df_basic[df_basic["artists"].apply(_is_primary_artist)]

        if df_basic.empty:
            return pd.DataFrame()

        # 3) Fetch detailed metadata
        album_ids = df_basic["id"].tolist()
        details = self.get_album_details(album_ids)
        df_details = pd.json_normalize(details) if details else pd.DataFrame(columns=["id"])

        # 4) Merge
        df = df_basic.merge(
            df_details[["id", "popularity", "label", "genres"]],
            on="id",
            how="left",
        )

        # 5) Filter to canonical Taylor Swift albums only
        df = df[df["name"].isin(TS_CANONICAL_ALBUMS)].copy()
        if df.empty:
            return pd.DataFrame()

        # 6) Classify versions: original vs rerecording vs deluxe
        name_series = df["name"].astype(str)

        # base_title strips "(Taylor's Version)" and "(deluxe version)"
        df["base_title"] = (
            name_series.str.replace(r"\s*\(Taylor's Version\)", "", regex=True, case=False)
            .str.replace(r"\s*\(deluxe version\)", "", regex=True, case=False)
            .str.strip()
        )

        # rerecordings = Taylor's Version
        df["is_rerecording"] = name_series.str.contains("Taylor's Version", case=False, regex=False)

        # deluxe = has "deluxe" in the name (covers folklore/evermore deluxe)
        df["is_deluxe"] = name_series.str.contains("deluxe", case=False, regex=False)

        # 7) Select final columns
        columns = [
            "id",
            "name",
            "base_title",
            "album_type",
            "total_tracks",
            "release_date",
            "release_date_precision",
            "popularity",
            "label",
            "genres",
            "is_rerecording",
            "is_deluxe",
            "artists",
            "external_urls.spotify",
        ]
        existing_cols = [c for c in columns if c in df.columns]
        return df[existing_cols]

    def get_artist_tracks_df(
        self,
        artist_id: str,
        include_groups: str = "album,single",
        market: Optional[str] = None,
        primary_artist_only: bool = True,
    ) -> "pd.DataFrame":
        """
        Build a track-level discography DataFrame for an artist.

        Each row is a track, with album-level metadata attached.

        Parameters
        ----------
        artist_id : str
            Spotify artist ID
        include_groups : str, default "album,single"
            Album types to include
        market : str, optional
            ISO 3166-1 alpha-2 country code
        primary_artist_only : bool, default True
            If True, only include albums where artist is primary artist

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns including:
            - album_id, album_name, album_type, album_release_date, album_popularity, album_label
            - track_id, track_name, track_number, disc_number, duration_ms, explicit
            - album_base_title, album_is_rerecording, album_is_deluxe

        Examples
        --------
        >>> sp = SpotifyClient()
        >>> df = sp.get_artist_tracks_df('06HL4z0CvFAxyc27GXpf02')
        >>> print(df[['track_name', 'album_name', 'duration_ms']])
        """
        import pandas as pd

        # 1) Get enriched, filtered album DataFrame
        albums_df = self.get_artist_albums_df(
            artist_id=artist_id,
            include_groups=include_groups,
            market=market,
            primary_artist_only=primary_artist_only,
        )
        if albums_df.empty:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []

        # 2) Loop over albums and fetch their tracks
        for _, album in albums_df.iterrows():
            album_id = album["id"]
            try:
                tracks = self.get_album_tracks(album_id, market=market)
            except Exception as e:
                print(f"[warning] Error fetching tracks for album {album_id}: {e}")
                continue

            for t in tracks:
                rows.append(
                    {
                        # album-level info
                        "album_id": album_id,
                        "album_name": album["name"],
                        "album_base_title": album.get("base_title"),
                        "album_type": album["album_type"],
                        "album_release_date": album["release_date"],
                        "album_popularity": album.get("popularity"),
                        "album_label": album.get("label"),
                        "album_is_rerecording": album.get("is_rerecording"),
                        "album_is_deluxe": album.get("is_deluxe"),
                        # track-level info
                        "track_id": t.get("id"),
                        "track_name": t.get("name"),
                        "track_number": t.get("track_number"),
                        "disc_number": t.get("disc_number"),
                        "duration_ms": t.get("duration_ms"),
                        "explicit": t.get("explicit"),
                        "is_local": t.get("is_local"),
                    }
                )

        df = pd.DataFrame(rows)

        # Optional light cleaning of text fields
        if not df.empty:
            for col in ["album_name", "album_base_title", "track_name"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

        return df