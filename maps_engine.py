import googlemaps
from datetime import datetime
from pathlib import Path

# ==========================================
# 1. CONFIGURATION
# ==========================================

API_KEY_PATH = Path("API Keys/Gemini_api_key.txt")

if not API_KEY_PATH.exists():
    raise RuntimeError("Google Maps API key not found.")

API_KEY = API_KEY_PATH.read_text().strip()
gmaps = googlemaps.Client(key=API_KEY)


# ==========================================
# 2. RAW DATA FETCH
# ==========================================

def _fetch_directions(origin: str, destination: str):
    return gmaps.directions(
        origin=origin,
        destination=destination,
        mode="driving",
        departure_time=datetime.now(),
        alternatives=True
    )


# ==========================================
# 3. TRAFFIC ANALYSIS
# ==========================================

def _analyze_route(route: dict) -> dict:
    leg = route["legs"][0]

    normal_sec = leg["duration"]["value"]
    traffic_sec = leg.get("duration_in_traffic", {}).get("value", normal_sec)

    congestion_ratio = traffic_sec / normal_sec

    if congestion_ratio <= 1.15:
        congestion = "CLEAR"
    elif congestion_ratio <= 1.4:
        congestion = "MODERATE"
    else:
        congestion = "HEAVY"

    return {
        "summary": route["summary"],
        "distance_text": leg["distance"]["text"],
        "distance_meters": leg["distance"]["value"],
        "duration_text": leg.get("duration_in_traffic", {}).get(
            "text", leg["duration"]["text"]
        ),
        "duration_seconds": traffic_sec,
        "delay_minutes": max(0, int((traffic_sec - normal_sec) / 60)),
        "congestion": congestion,
        "destination": leg["end_address"].split(",")[0],
        "start_address": leg["start_address"]
    }


# ==========================================
# 4. PUBLIC API
# ==========================================

def get_route_data(origin: str, destination: str, traffic: bool = False) -> dict:
    """
    Returns structured route + traffic information.
    """
    try:
        directions = _fetch_directions(origin, destination)
        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        primary = _analyze_route(directions[0])
        alternatives = []

        for alt in directions[1:]:
            alternatives.append(_analyze_route(alt))

        return {
            "origin": origin,
            "destination": destination,
            "traffic_query": traffic,
            "primary_route": primary,
            "alternative_routes": alternatives
        }

    except Exception as e:
        return {
            "error": "MAPS_API_ERROR",
            "details": str(e)
        }
