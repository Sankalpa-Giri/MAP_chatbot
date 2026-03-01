# maps_engine.py
import re
import logging
import googlemaps
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ==========================================
# 1. CONFIGURATION
# ==========================================

API_KEY_PATH = Path("API Keys/Google_maps_api_key.txt")  # fixed: was pointing to Gemini key

if not API_KEY_PATH.exists():
    raise RuntimeError(f"Google Maps API key not found at {API_KEY_PATH}")

API_KEY = API_KEY_PATH.read_text().strip()
gmaps = googlemaps.Client(key=API_KEY)


# ==========================================
# 2. RAW DATA FETCH
# ==========================================

def _fetch_directions(origin: str, destination: str, alternatives: bool = True) -> list:
    return gmaps.directions(  # type: ignore
        origin=origin,
        destination=destination,
        mode="driving",
        departure_time=datetime.now(),
        alternatives=alternatives
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
# 4. STEP PARSER
# ==========================================

def _parse_steps(route: dict) -> list[dict]:
    """Extract and clean turn-by-turn steps from a raw directions route."""
    try:
        steps = route["legs"][0]["steps"]
        return [
            {
                "instruction": re.sub(r"<[^>]+>", "", step["html_instructions"]).strip(),
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"]
            }
            for step in steps
        ]
    except (KeyError, IndexError) as e:
        logger.warning(f"Step parsing failed: {e}")
        return []


# ==========================================
# 5. PUBLIC API
# ==========================================

def get_route_data(origin: str, destination: str, traffic: bool = False) -> dict:
    """
    Returns primary + alternative route summaries with traffic analysis.
    Does not include step-by-step instructions — use get_route_steps for those.
    """
    try:
        directions = _fetch_directions(origin, destination, alternatives=True)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        primary = _analyze_route(directions[0])
        alternatives = [_analyze_route(alt) for alt in directions[1:]]

        return {
            "origin": origin,
            "destination": destination,
            "traffic_query": traffic,
            "primary_route": primary,
            "alternative_routes": alternatives
        }

    except Exception as e:
        logger.error(f"get_route_data failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}


def get_route_steps(origin: str, destination: str) -> list[dict]:
    """
    Returns step-by-step turn instructions for the primary route.
    Makes a separate API call with alternatives=False for efficiency.

    Returns:
        [{"instruction": str, "distance": str, "duration": str}, ...]
    """
    try:
        directions = _fetch_directions(origin, destination, alternatives=False)

        if not directions:
            logger.warning("get_route_steps: no directions returned")
            return []

        return _parse_steps(directions[0])

    except Exception as e:
        logger.error(f"get_route_steps failed: {e}")
        return []