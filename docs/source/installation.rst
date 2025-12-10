Installation
============

Prerequisites
-------------
- Python 3.13+
- API keys for Spotify and NYT

From Source
-----------
.. code-block:: bash

   git clone https://github.com/yourusername/ts-media-bridge.git
   cd ts-media-bridge
   pip install -e .

API Keys Setup
--------------
Create a `.env` file in the project root:
.. code-block:: bash

   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   NYT_API_KEY=your_nyt_api_key
