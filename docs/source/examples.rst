Examples
========

Get Artist Albums
-----------------
.. code-block:: python

   from ts_media_bridge import SpotifyClient

   sp = SpotifyClient()
   df_albums = sp.get_artist_albums_df("06HL4z0CvFAxyc27GXpf02")
   print(df_albums[['name', 'release_date', 'popularity']])

Search NYT by Date Range
-------------------------
.. code-block:: python

   from ts_media_bridge import NYTClient

   nyt = NYTClient()
   docs = nyt.search_articles(
       query="Taylor Swift",
       pages=3,
       begin_date="20200101",
       end_date="20221231"
   )
   df_articles = nyt.docs_to_df(docs)

Compare Re-recordings
---------------------
.. code-block:: python

   from ts_media_bridge import compare_rerecordings

   df_tracks = sp.get_artist_tracks_df("06HL4z0CvFAxyc27GXpf02")
   comparison = compare_rerecordings(df_tracks)
   print(comparison)
