import googlemaps
from datetime import datetime
from pathlib import Path
import re

API_KEY_PATH = Path("API Keys/maps_key.txt")
if not API_KEY_PATH.exists():
    raise RuntimeError("Google Maps API key not found.")

API_KEY = API_KEY_PATH.read_text().strip()
gmaps = googlemaps.Client(key=API_KEY)

# Bhubaneswar coordinates
BHUBANESWAR_CENTER = {"lat": 20.2961, "lng": 85.8245}

# ==========================================
# CLEAN NAME FOR TTS
# ==========================================

def clean_name_for_tts(name: str) -> str:
    """Remove non-English characters for better TTS"""
    # Split by comma
    parts = name.split(",")
    
    for part in parts:
        part_clean = part.strip()
        # Keep only English alphanumeric + common punctuation
        if re.match(r'^[a-zA-Z0-9\s\-\'()&.]+$', part_clean):
            return part_clean
    
    # Fallback
    return name.split(",")[0].strip()

# ==========================================
# FIND PLACE (Bhubaneswar-centric)
# ==========================================

def find_place(query: str, prefer_bhubaneswar: bool = True) -> dict:
    """
    Find a place with Bhubaneswar bias
    """
    try:
        if prefer_bhubaneswar:
            # Try with "Bhubaneswar" context first
            search_query = f"{query}, Bhubaneswar, Odisha"
            results = gmaps.geocode(search_query, region="in", language="en")
            
            if not results:
                # Fallback without Bhubaneswar
                results = gmaps.geocode(query, region="in", language="en")
        else:
            # General search (for places outside Bhubaneswar)
            results = gmaps.geocode(query, region="in", language="en")
        
        if not results:
            return None
        
        result = results[0]
        location = result["geometry"]["location"]
        
        # Extract clean name
        clean_place_name = None
        
        for component in result.get("address_components", []):
            types = component["types"]
            name = component["long_name"]
            
            # Look for actual place names
            if any(t in types for t in ["point_of_interest", "establishment", "premise", "tourist_attraction"]):
                # Skip Plus Codes
                if not re.match(r'^[A-Z0-9]{4}\+[A-Z0-9]{2,}$', name):
                    clean_place_name = name
                    break
        
        # Fallback to formatted address
        if not clean_place_name:
            formatted = result["formatted_address"]
            first_part = formatted.split(",")[0].strip()
            
            # Skip Plus Codes
            if not re.match(r'^[A-Z0-9]{4}\+[A-Z0-9]{2,}', first_part):
                clean_place_name = first_part
            else:
                # Use query as name
                clean_place_name = query.title()
        
        print(f"✅ Found: {clean_name_for_tts(clean_place_name)}")
        
        return {
            "coords": location,
            "name": clean_name_for_tts(clean_place_name),
            "full_address": result["formatted_address"]
        }
        
    except Exception as e:
        print(f"❌ Error finding '{query}': {e}")
        return None

# ==========================================
# GET ROUTE DATA (Main Function)
# ==========================================

def get_route_data(origin: str, destination: str, get_steps: bool = False) -> dict:
    """
    Get route with traffic info (Bhubaneswar-centric)
    """
    try:
        # Determine if destination is likely outside Bhubaneswar
        dest_lower = destination.lower()
        outside_odisha_keywords = [
            "delhi", "mumbai", "bangalore", "kolkata", "chennai", "pune",
            "hyderabad", "ahmedabad", "jaipur", "lucknow", "kanpur",
            "agra", "taj mahal", "india gate", "gateway of india",
            "connaught place", "marine drive"
        ]
        
        prefer_bbsr = not any(keyword in dest_lower for keyword in outside_odisha_keywords)
        
        print(f"🔍 Searching for: {origin}")
        origin_data = find_place(origin, prefer_bhubaneswar=True)
        
        print(f"🔍 Searching for: {destination}")
        dest_data = find_place(destination, prefer_bhubaneswar=prefer_bbsr)
        
        if not origin_data:
            return {"error": "ORIGIN_NOT_FOUND", "message": f"Could not find '{origin}'"}
        if not dest_data:
            return {"error": "DESTINATION_NOT_FOUND", "message": f"Could not find '{destination}'"}
        
        print(f"🗺️ Route: {origin_data['name']} → {dest_data['name']}")
        
        # Get directions with traffic
        directions = gmaps.directions(
            origin=origin_data["coords"],
            destination=dest_data["coords"],
            mode="driving",
            departure_time=datetime.now(),
            alternatives=False,
            traffic_model="best_guess"
        )
        
        if not directions:
            return {"error": "NO_ROUTE_FOUND"}
        
        route = directions[0]
        leg = route["legs"][0]
        
        # TRAFFIC CALCULATION
        normal_sec = leg["duration"]["value"]
        traffic_sec = leg.get("duration_in_traffic", {}).get("value", normal_sec)
        delay_mins = (traffic_sec - normal_sec) / 60
        
        distance_km = leg["distance"]["value"] / 1000
        hour = datetime.now().hour
        is_peak = (9 <= hour <= 11) or (17 <= hour <= 20)
        
        # Traffic status
        if delay_mins > 8:
            traffic_msg = "Heavy traffic"
        elif delay_mins > 3 or (is_peak and distance_km < 15):
            traffic_msg = "Moderate traffic"
        else:
            traffic_msg = "Traffic is light"
        
        result = {
            "origin": origin_data["name"],
            "destination": dest_data["name"],
            "route_name": route["summary"],
            "distance": leg["distance"]["text"],
            "duration": leg.get("duration_in_traffic", {}).get("text", leg["duration"]["text"]),
            "traffic_desc": traffic_msg
        }
        
        # Add turn-by-turn directions if requested
        if get_steps:
            steps = []
            for i, step in enumerate(leg["steps"]):
                if i >= 3:
                    break
                instruction = step["html_instructions"]
                instruction = re.sub('<.*?>', '', instruction)
                instruction = re.sub(r'&nbsp;', ' ', instruction)
                instruction = ' '.join(instruction.split())
                steps.append(instruction)
            result["steps"] = steps
        
        return result
        
    except Exception as e:
        print(f"❌ Maps error: {e}")
        return {"error": "ERROR", "details": str(e)}