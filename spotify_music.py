import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
import os

# ==========================================
# 1. CONFIGURATION (ENV BASED)
# ==========================================

#SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_ID = '95699f03708345b0819b32540d84dac6'
#SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_CLIENT_SECRET = '7512970f8ec04ec28c72c4a60a6cfa23'
#SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'

SCOPE = "user-read-playback-state"

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise RuntimeError("Spotify credentials not set in environment variables.")


def _get_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotify_cache"
        )
    )


# ==========================================
# 2. SEARCH ENGINE (NO PLAYBACK)
# ==========================================

def search_track(query: str) -> dict:
    """
    Searches Spotify and returns track metadata.
    Does NOT start playback.
    """

    try:
        sp = _get_spotify_client()
        result = sp.search(q=query, limit=1, type="track")

        if not result["tracks"]["items"]:
            return {"error": "TRACK_NOT_FOUND", "query": query}

        track = result["tracks"]["items"][0]

        return {
            "track_name": track["name"],
            "artist": track["artists"][0]["name"],
            "uri": track["uri"],
            "album": track["album"]["name"],
            "duration_ms": track["duration_ms"],
            "preview_url": track["preview_url"]
        }

    except Exception as e:
        return {
            "error": "SPOTIFY_SEARCH_FAILED",
            "details": str(e)
        }
