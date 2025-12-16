import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# ==========================================
# 1. CONFIGURATION
# ==========================================
SPOTIPY_CLIENT_ID = '95699f03708345b0819b32540d84dac6'
SPOTIPY_CLIENT_SECRET = '7512970f8ec04ec28c72c4a60a6cfa23'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'

# Scope: We need permission to read state AND modify playback
SCOPE = "user-modify-playback-state,user-read-playback-state"

def get_spotify_client():
    """Returns an authenticated spotipy client instance."""
    # We add a specific 'cache_path' to ensure the token is saved safely
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_cache_shift"
    ))

def get_active_device_id(sp):
    """
    Finds a device ID. Prioritizes active devices, falls back to the first available one.
    """
    try:
        devices = sp.devices()
        
        if not devices or not devices['devices']:
            return None
        
        # 1. Look for an already active device (Playing music right now)
        for device in devices['devices']:
            if device['is_active']:
                return device['id']
                
        # 2. If no active device, pick the first one (e.g., Laptop or Phone)
        # This usually wakes up the Spotify app on that device.
        return devices['devices'][0]['id']
        
    except Exception as e:
        print(f"Device Search Error: {e}")
        return None

def play_music(query):
    """
    Searches for a song/artist and plays it on the active device.
    """
    try:
        # A. Authenticate
        sp = get_spotify_client()

        # B. Find Device
        device_id = get_active_device_id(sp)
        if not device_id:
            return "No active Spotify device found. Please open Spotify on your laptop or phone."

        # C. Search
        print(f"🎵 Searching Spotify for: {query}")
        # We append 'track' to the query type to be specific
        result = sp.search(q=query, limit=1, type='track')
        
        if not result['tracks']['items']:
            # Fallback: Try searching for artist if track not found
            result = sp.search(q=query, limit=1, type='artist')
            if not result['artists']['items']:
                return f"I couldn't find music matching '{query}'."
            # If artist found, play their top tracks context (logic differs, sticking to track for now)
            return f"I couldn't find the song '{query}', but found the artist. (Artist playback requires different logic)."

        # D. Get Track Details
        track = result['tracks']['items'][0]
        track_uri = track['uri']
        track_name = track['name']
        artist_name = track['artists'][0]['name']

        # E. THE ROBUST PLAYBACK LOGIC
        # 1. Transfer playback first to wake up the device
        # 'force_play=False' avoids starting the OLD song before the NEW one
        sp.transfer_playback(device_id=device_id, force_play=False)
        
        # Small delay to let the transfer happen
        time.sleep(0.5) 
        
        # 2. Start the new song
        sp.start_playback(device_id=device_id, uris=[track_uri])
        
        return f"Playing {track_name} by {artist_name}."

    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        if e.http_status == 404:
            return "Device not found. Please wake up your Spotify app."
        elif e.http_status == 403:
            return "Spotify Premium is required for playback control."
        else:
            return "I had trouble talking to Spotify."
            
    except Exception as e:
        print(f"General Music Error: {e}")
        return "Something went wrong with the music engine."

# Test
if __name__ == "__main__":
    # Ensure Spotify is OPEN and logged into your Premium account
    print(play_music("Sanam Teri kasam"))