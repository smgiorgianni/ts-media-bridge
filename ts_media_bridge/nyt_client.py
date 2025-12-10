from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


NYT_BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


class NYTAuthError(RuntimeError):
    """Raised when NYT API authentication fails."""


class NYTClient:
    """
    Minimal NYT Article Search API client.

    - Reads NYT_API_KEY from .env or environment
    - Provides search_articles() for general queries
    - Provides search_taylor_swift() and search_album() helpers
    - docs_to_df() converts raw docs to a clean DataFrame
    - Implements smart rate limiting to avoid 429 errors
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("NYT_API_KEY")
        if not self.api_key:
            raise NYTAuthError(
                "Missing NYT_API_KEY. Add it to your .env file or environment."
            )
        
        # Rate limiting: NYT allows 10 calls per minute
        self._last_request_time = 0.0
        self._min_request_interval = 6.5  # Wait 6.5 seconds between requests (safer than 6)

    def _rate_limit_wait(self) -> None:
        """
        Ensure we don't exceed rate limits by waiting between requests.
        NYT allows 10 calls per minute, so we wait at least 6 seconds between calls.
        """
        now = time.time()
        time_since_last = now - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            print(f"[NYT] Rate limiting: waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()

    def _get(
        self,
        query: str,
        page: int = 0,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Internal helper: perform a single NYT Article Search request,
        with rate limiting and handling for HTTP 429.
        """
        params = {
            "q": query,
            "api-key": self.api_key,
            "page": page,
        }
        if begin_date:
            params["begin_date"] = begin_date
        if end_date:
            params["end_date"] = end_date

        last_status: Optional[int] = None

        for attempt in range(max_retries):
            # Wait before each request to respect rate limits
            self._rate_limit_wait()
            
            resp = requests.get(NYT_BASE_URL, params=params, timeout=15)
            last_status = resp.status_code

            # Handle rate limiting
            if resp.status_code == 429:
                wait = 2 ** (attempt + 3)  # 8, 16, 32 seconds
                print(
                    f"[NYT] Rate limit hit (429) despite precautions! "
                    f"Waiting {wait}s before retry {attempt + 1}/{max_retries}..."
                )
                time.sleep(wait)
                continue

            # Any other non-OK status: raise
            resp.raise_for_status()
            return resp.json()

        raise RuntimeError(
            f"NYT API failed after {max_retries} retries "
            f"(last status {last_status})."
        )

    # ---------------- Public methods ---------------- #

    def search_articles(
        self,
        query: str,
        pages: int = 1,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        General Article Search.

        Parameters
        ----------
        query : str
            Free text query, passed as 'q' to NYT.
        pages : int
            Number of result pages to request (0-indexed pages).
        begin_date, end_date : str or None
            Optional date filters in YYYYMMDD format, e.g. "20100101".

        Returns
        -------
        List[dict]
            List of NYT 'doc' objects.
        """
        all_docs: List[Dict[str, Any]] = []

        for p in range(pages):
            js = self._get(
                query=query,
                page=p,
                begin_date=begin_date,
                end_date=end_date,
            )
            docs = js.get("response", {}).get("docs", [])
            if not docs:
                break
            all_docs.extend(docs)

        return all_docs

    def search_taylor_swift(
        self,
        pages: int = 2,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper for general 'Taylor Swift' coverage.
        """
        return self.search_articles(
            query="Taylor Swift",
            pages=pages,
            begin_date=begin_date,
            end_date=end_date,
        )

    def search_album(
        self,
        album_name: str,
        pages: int = 1,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search NYT for articles likely about a specific Taylor Swift album,
        by querying both the album name and 'Taylor Swift' together.

        Example query:
            "\"1989\" \"Taylor Swift\""
        """
        query = f'"{album_name}" "Taylor Swift"'
        return self.search_articles(
            query=query,
            pages=pages,
            begin_date=begin_date,
            end_date=end_date,
        )

    def docs_to_df(self, docs: List[Dict[str, Any]]):
        """
        Convert NYT article docs into a tidy pandas DataFrame.

        Columns:
        - pub_date
        - headline
        - snippet
        - section
        - source
        - news_desk
        - type_of_material
        - web_url
        """
        import pandas as pd

        if not docs:
            return pd.DataFrame()

        rows = []
        for d in docs:
            rows.append(
                {
                    "pub_date": d.get("pub_date"),
                    "headline": d.get("headline", {}).get("main"),
                    "snippet": d.get("snippet"),
                    "section": d.get("section_name"),
                    "source": d.get("source"),
                    "news_desk": d.get("news_desk"),
                    "type_of_material": d.get("type_of_material"),
                    "web_url": d.get("web_url"),
                }
            )

        return pd.DataFrame(rows)