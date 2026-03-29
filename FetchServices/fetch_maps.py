# maps_engine.py
import re
import logging
import googlemaps
from datetime import datetime, timedelta
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
# 2. DESTINATION BIAS — nearest-match via Places API
# ==========================================

# Generic category words — "nearest X" queries use distance-ranked nearby search
# Generic category words — resolve to physically nearest place.
_CATEGORY_KEYWORDS = {
    "hospital", "clinic", "airport", "bus stand", "bus station",
    "railway station", "train station", "metro station", "petrol pump",
    "petrol station", "fuel station", "gas station", "pharmacy", "chemist",
    "police station", "fire station", "atm", "bank", "school", "college",
    "restaurant", "hotel", "cafe", "coffee shop", "mall", "market",
    "temple", "church", "mosque", "park", "stadium"
}

# Proximity prefixes to strip before category/named-place lookup.
_PROXIMITY_PREFIXES = ("nearest ", "closest ", "nearby ", "near ")


def _strip_proximity(text: str) -> str:
    """Remove leading proximity qualifiers: 'nearest hospital' → 'hospital'."""
    cleaned = text.lower().strip()
    for prefix in _PROXIMITY_PREFIXES:
        if cleaned.startswith(prefix):
            return cleaned[len(prefix):]
    return cleaned


def _get_city_name(lat: float, lon: float) -> str:
    """
    Reverse-geocodes the driver's coordinates to extract the city name.
    Used to append city context to short/ambiguous named queries so that
    find_place("aiims bhubaneswar") beats find_place("aiims") → Delhi.
    Returns empty string on failure (caller handles gracefully).
    """
    try:
        results = gmaps.reverse_geocode(  # type: ignore
            (lat, lon),
            result_type=["locality"]
        )
        if results:
            for component in results[0].get("address_components", []):
                if "locality" in component.get("types", []):
                    return component["long_name"]
    except Exception as e:
        logger.warning(f"_get_city_name reverse_geocode failed: {e}")
    return ""


def _is_category_search(destination: str) -> bool:
    """Returns True when destination is a generic category rather than a named place."""
    return _strip_proximity(destination) in _CATEGORY_KEYWORDS


def _resolve_category(keyword: str, lat: float, lon: float) -> str | None:
    """
    For generic categories (hospital, airport, etc.) use places_nearby with
    rank_by="distance" — strict distance ordering, no prominence weighting.
    rank_by="distance" is mutually exclusive with radius in the Places API.
    """
    cleaned = _strip_proximity(keyword)
    try:
        results = gmaps.places_nearby(  # type: ignore
            location={"lat": lat, "lng": lon},
            rank_by="distance",
            keyword=cleaned
        )
        places = results.get("results", [])
        if places:
            top      = places[0]
            name     = top.get("name", "")
            vicinity = top.get("vicinity", "")
            resolved = f"{name}, {vicinity}" if vicinity else name
            logger.info(f"_resolve_category: '{keyword}' → '{resolved}'")
            return resolved
    except Exception as e:
        logger.warning(f"_resolve_category failed for '{keyword}': {e}")
    return None


def _resolve_named_place(name: str, lat: float, lon: float) -> str | None:
    """
    For specific named institutions (AIIMS, Silicon University, Zudio) use
    find_place() with two strategies tried in order:

    1. Query with city name appended: "aiims bhubaneswar"
       Appending the city defeats global prominence bias for short acronyms
       and institution names that exist in multiple cities.

    2. Query with location_bias only (no city suffix) as fallback.
       Handles cases where the city lookup fails or the name already
       contains enough context.

    A 50 km circle bias is used — soft preference, not a hard cutoff,
    so institutions 18-30 km away are still found correctly.
    """
    city = _get_city_name(lat, lon)

    # Strategy 1: name + city suffix (most reliable for short acronyms)
    if city:
        query_with_city = f"{name} {city}"
        try:
            result = gmaps.find_place(  # type: ignore
                input=query_with_city,
                input_type="textquery",
                fields=["name", "formatted_address"],
                location_bias=f"circle:50000@{lat},{lon}"
            )
            candidates = result.get("candidates", [])
            if candidates:
                resolved = candidates[0].get("formatted_address", "")
                if resolved:
                    logger.info(f"_resolve_named_place (with city): '{name}' → '{resolved}'")
                    return resolved
        except Exception as e:
            logger.warning(f"_resolve_named_place city-query failed for '{name}': {e}")

    # Strategy 2: name only with location bias
    try:
        result = gmaps.find_place(  # type: ignore
            input=name,
            input_type="textquery",
            fields=["name", "formatted_address"],
            location_bias=f"circle:50000@{lat},{lon}"
        )
        candidates = result.get("candidates", [])
        if candidates:
            resolved = candidates[0].get("formatted_address", "")
            if resolved:
                logger.info(f"_resolve_named_place (bias only): '{name}' → '{resolved}'")
                return resolved
    except Exception as e:
        logger.warning(f"_resolve_named_place bias-query failed for '{name}': {e}")

    return None


def _bias_destination(destination: str, origin: str) -> str:
    """
    Resolves an ambiguous destination to the correct local place.

    Generic category ("hospital", "nearest airport")
      → _resolve_category: places_nearby rank_by=distance
        The physically closest matching place always wins.

    Named place ("AIIMS", "aiims", "Silicon University", "Zudio")
      → _resolve_named_place: find_place with city-name suffix + location bias
        Appending the driver's city to the query ("aiims bhubaneswar") defeats
        global prominence bias that would otherwise resolve short acronyms like
        "aiims" to the nationally most famous instance (Delhi) regardless of
        the driver's actual location.

    Falls back to the raw destination string if both strategies fail.
    """
    try:
        lat_str, lon_str = origin.split(",")
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
    except (ValueError, AttributeError):
        return destination

    if _is_category_search(destination):
        resolved = _resolve_category(destination, lat, lon)
    else:
        resolved = _resolve_named_place(destination, lat, lon)

    if resolved:
        return resolved

    logger.info(f"_bias_destination: no result for '{destination}', using raw string")
    return destination
# ==========================================
# 3. RAW DATA FETCH
# ==========================================

def _fetch_directions(
    origin: str,
    destination: str,
    alternatives: bool = True,
    traffic: bool = True
) -> list:
    """
    Fetches directions from Google Maps.
    departure_time is only passed when traffic=True to enable
    duration_in_traffic without unnecessary API overhead.
    """
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
# 4. TRAFFIC ANALYSIS
# ==========================================

def _analyze_route(route: dict) -> dict:
    """
    Analyses a single route leg and returns a normalised summary dict.
    Congestion levels: CLEAR | MODERATE | HEAVY

    Uses route.get("summary", "") instead of route["summary"] so transits
    or walking routes that omit the summary field don't raise a KeyError.
    """
    leg = route["legs"][0]

    normal_sec  = leg["duration"]["value"]
    traffic_sec = leg.get("duration_in_traffic", {}).get("value", normal_sec)
    congestion_ratio = traffic_sec / normal_sec

    if congestion_ratio <= 1.15:
        congestion = "CLEAR"
    elif congestion_ratio <= 1.4:
        congestion = "MODERATE"
    else:
        congestion = "HEAVY"

    return {
        "summary":        route.get("summary", ""),   # safe — some routes omit this
        "distance_text":  leg["distance"]["text"],
        "distance_meters":leg["distance"]["value"],
        "duration_text":  leg.get("duration_in_traffic", {}).get(
                              "text", leg["duration"]["text"]
                          ),
        "duration_seconds": traffic_sec,
        "delay_minutes":  max(0, int((traffic_sec - normal_sec) / 60)),
        "congestion":     congestion,
        "destination":    leg["end_address"].split(",")[0],
        "start_address":  leg["start_address"]
    }


# ==========================================
# 5. STEP PARSER
# ==========================================

def _parse_steps(route: dict) -> list[dict]:
    """Extract and clean turn-by-turn steps from a raw directions route."""
    try:
        steps = route["legs"][0]["steps"]
        parsed = []
        for step in steps:
            html = step["html_instructions"]
            # Google wraps secondary text ("Pass by ...") in <div> with no
            # surrounding whitespace — replace block tags with a space before
            # stripping all remaining tags, then collapse double spaces.
            spaced      = re.sub(r"</?(div|wbr)[^>]*>", " ", html, flags=re.IGNORECASE)
            instruction = re.sub(r"<[^>]+>", "", spaced).strip()
            instruction = re.sub(r" {2,}", " ", instruction)
            parsed.append({
                "instruction": instruction,
                "distance":    step["distance"]["text"],
                "duration":    step["duration"]["text"]
            })
        return parsed
    except (KeyError, IndexError) as e:
        logger.warning(f"Step parsing failed: {e}")
        return []


# ==========================================
# 6. PUBLIC API
# ==========================================

def get_route_data(origin: str, destination: str, traffic: bool = False) -> dict:
    """
    Returns primary + alternative route summaries with optional traffic data.
    Destination is bias-resolved to the nearest matching place before the
    Directions call so ambiguous names (airport, AIIMS) resolve locally.
    """
    try:
        destination = _bias_destination(destination, origin)
        directions  = _fetch_directions(origin, destination, alternatives=True, traffic=traffic)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        primary      = _analyze_route(directions[0])
        alternatives = [_analyze_route(alt) for alt in directions[1:]]

        return {
            "origin":             origin,
            "destination":        destination,
            "traffic_query":      traffic,
            "primary_route":      primary,
            "alternative_routes": alternatives
        }

    except Exception as e:
        logger.error(f"get_route_data failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}


def get_route_steps(origin: str, destination: str) -> list[dict]:
    """
    Returns step-by-step turn instructions for the primary route.
    Bias-resolves destination for consistency with get_route_data().
    """
    try:
        destination = _bias_destination(destination, origin)
        directions  = _fetch_directions(origin, destination, alternatives=False, traffic=False)

        if not directions:
            logger.warning("get_route_steps: no directions returned")
            return []

        return _parse_steps(directions[0])

    except Exception as e:
        logger.error(f"get_route_steps failed: {e}")
        return []


def get_traffic_status(origin: str, destination: str) -> dict:
    """
    Returns real-time traffic summary: congestion, delay minutes, and ETA.
    Used by traffic_status_handler for GET_TRAFFIC and GET_ETA intents.
    """
    try:
        destination = _bias_destination(destination, origin)
        directions  = _fetch_directions(origin, destination, alternatives=False, traffic=True)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        analysis = _analyze_route(directions[0])

        eta_dt = datetime.now().replace(second=0, microsecond=0)
        eta_dt = eta_dt + timedelta(seconds=analysis["duration_seconds"])
        # "%I:%M %p" + lstrip("0") is cross-platform; "%-I" is Linux-only
        analysis["eta"] = eta_dt.strftime("%I:%M %p").lstrip("0")

        return analysis

    except Exception as e:
        logger.error(f"get_traffic_status failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}


def get_distance_duration(origin: str, destination: str) -> dict:
    """
    Returns distance and free-flow travel time (no live traffic).
    Used by traffic_status_handler for GET_DISTANCE intent.
    """
    try:
        destination = _bias_destination(destination, origin)
        directions  = _fetch_directions(origin, destination, alternatives=False, traffic=False)

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        leg = directions[0]["legs"][0]
        return {
            "distance_text":   leg["distance"]["text"],
            "distance_meters": leg["distance"]["value"],
            "duration_text":   leg["duration"]["text"],
            "duration_seconds":leg["duration"]["value"],
            "destination":     leg["end_address"].split(",")[0]
        }

    except Exception as e:
        logger.error(f"get_distance_duration failed: {e}")
        return {"error": "MAPS_API_ERROR", "details": str(e)}