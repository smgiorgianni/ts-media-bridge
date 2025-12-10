Quick Start
===========

Basic Usage
-----------
.. code-block:: python

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
