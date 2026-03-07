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

API_KEY_PATH = Path("API Keys/Google_maps_api_key.txt")

if not API_KEY_PATH.exists():
    raise RuntimeError(f"Google Maps API key not found at {API_KEY_PATH}")

API_KEY = API_KEY_PATH.read_text().strip()
gmaps = googlemaps.Client(key=API_KEY)


# ==========================================
# 2. RAW DATA FETCH
# ==========================================

def _fetch_directions(origin: str, destination: str, alternatives: bool = True, traffic: bool = True) -> list:
    """
    Fetches directions from Google Maps.
    FIX: Added `traffic` parameter. When traffic=True, departure_time=now() is passed
    to enable duration_in_traffic in the response. When False, it is omitted —
    previously the departure_time was always sent, making the `traffic` flag in
    get_route_data() a no-op.
    """
    # FIX: departure_time is passed as a direct keyword argument conditionally,
    # not via a dict. The googlemaps stub types kwargs as dict[str, str | bool],
    # which rejects datetime — explicit keyword args bypass that entirely.
    if traffic:
        return gmaps.directions(  # type: ignore
            origin=origin,
            destination=destination,
            mode="driving",
            alternatives=alternatives,
            departure_time=datetime.now()
        )
    return gmaps.directions(  # type: ignore
        origin=origin,
        destination=destination,
        mode="driving",
        alternatives=alternatives
    )


# ==========================================
# 3. TRAFFIC ANALYSIS
# ==========================================

def _analyze_route(route: dict) -> dict:
    """
    Analyses a single route leg for traffic congestion and delay.
    Congestion levels: CLEAR | MODERATE | HEAVY
    These are the canonical values used across all handlers.
    """
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
        parsed = []
        for step in steps:
            html = step["html_instructions"]
            # FIX: Google Maps wraps secondary text (e.g. "Pass by ...") in <div>
            # tags. Stripping tags with a bare regex leaves no space between the
            # main instruction and the secondary text — e.g. "...RdPass by...".
            # Replace every closing block tag with a space first, then strip all
            # remaining tags, then collapse any double spaces.
            spaced = re.sub(r"</?(div|wbr)[^>]*>", " ", html, flags=re.IGNORECASE)
            instruction = re.sub(r"<[^>]+>", "", spaced).strip()
            instruction = re.sub(r" {2,}", " ", instruction)
            parsed.append({
                "instruction": instruction,
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"]
            })
        return parsed
    except (KeyError, IndexError) as e:
        logger.warning(f"Step parsing failed: {e}")
        return []


# ==========================================
# 5. PUBLIC API
# ==========================================

def get_route_data(origin: str, destination: str, traffic: bool = False) -> dict:
    """
    Returns primary + alternative route summaries with optional traffic analysis.
    Does not include step-by-step instructions — use get_route_steps() for those.

    FIX: `traffic` parameter is now honoured — passed down to _fetch_directions
    so that duration_in_traffic is only requested when actually needed.
    """
    try:
        directions = _fetch_directions(origin, destination, alternatives=True, traffic=traffic)

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
        directions = _fetch_directions(origin, destination, alternatives=False, traffic=False)

        if not directions:
            logger.warning("get_route_steps: no directions returned")
            return []

        return _parse_steps(directions[0])

    except Exception as e:
        logger.error(f"get_route_steps failed: {e}")
        return []


def get_traffic_status(origin: str, destination: str) -> dict:
    """
    NEW — Returns real-time traffic summary for a route: congestion level,
    delay in minutes, and ETA (estimated arrival time as a formatted string).

    Used by traffic_status_handler for GET_TRAFFIC and GET_ETA intents.

    Returns:
        {
            "congestion": "CLEAR" | "MODERATE" | "HEAVY",
            "delay_minutes": int,
            "duration_text": str,       # travel time with traffic
            "duration_seconds": int,
            "eta": str,                 # e.g. "2:45 PM"
            "destination": str,
            "distance_text": str
        }
    """
    try:
        directions = _fetch_directions(origin, destination, alternatives=False, traffic=True)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        analysis = _analyze_route(directions[0])

        # Compute ETA = now + travel time (with traffic)
        eta_dt = datetime.now().replace(second=0, microsecond=0)
        from datetime import timedelta
        eta_dt = eta_dt + timedelta(seconds=analysis["duration_seconds"])
        # FIX: "%-I" strips the leading zero on Linux only — crashes on Windows.
        # Use "%I:%M %p" and strip the leading zero manually for cross-platform safety.
        analysis["eta"] = eta_dt.strftime("%I:%M %p").lstrip("0")  # e.g. "2:45 PM"

        return analysis

    except Exception as e:
        logger.error(f"get_traffic_status failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}


def get_distance_duration(origin: str, destination: str) -> dict:
    """
    NEW — Returns distance and estimated travel time (without live traffic)
    for a clean "how far / how long" reply.

    Used by traffic_status_handler for GET_DISTANCE intent.

    Returns:
        {
            "distance_text": str,       # e.g. "12.4 km"
            "distance_meters": int,
            "duration_text": str,       # e.g. "18 mins"
            "duration_seconds": int,
            "destination": str
        }
    """
    try:
        # traffic=False → no departure_time → duration reflects free-flow estimate
        directions = _fetch_directions(origin, destination, alternatives=False, traffic=False)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        leg = directions[0]["legs"][0]
        return {
            "distance_text": leg["distance"]["text"],
            "distance_meters": leg["distance"]["value"],
            "duration_text": leg["duration"]["text"],
            "duration_seconds": leg["duration"]["value"],
            "destination": leg["end_address"].split(",")[0]
        }

    except Exception as e:
        logger.error(f"get_distance_duration failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}