# weather_handler.py
import logging
import conversation_store
from conversation_store import Session
from FetchServices import fetch_weather
from Generate import generate_response_weather

logger = logging.getLogger(__name__)


# ==========================================
# INTERNAL HELPERS
# ==========================================

def _get_origin_coords(user_location: dict) -> tuple[float, float] | None:
    """
    Extracts (lat, lon) from the user_location dict.
    Returns None if either coordinate is missing.
    Uses `is not None` so that 0.0 (valid equator coordinate) is not rejected.
    """
    lat = user_location.get("latitude")
    lon = user_location.get("longitude")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    return None


def _resolve_city(routeInfo: dict, state: Session) -> str | None:
    """
    Resolves the target city from NLU entities or session history.
    Returns the city string, or None if the destination is referential/missing
    (caller should fall back to GPS in that case).
    """
    entities    = routeInfo.get("entities", {})
    is_dependent = routeInfo.get("is_dependent", False)

    city = entities.get("destination")

    # Referential words ("there", "here", "it") are cleared to None by
    # identify_intent — is_dependent=True signals to look at history instead.
    if not city and is_dependent:
        city = state.last_location

    # Guard whitespace-only strings
    if city and city.strip():
        return city.strip()

    return None


# ==========================================
# ACTION
# ==========================================

def weather_action(routeInfo: dict, text: str, session_id: str) -> dict:
    """
    Handles GET_WEATHER intent.

    Resolution priority:
      1. Named city from NLU entity  → get_weather_report(city)
      2. Referential / no city       → get_weather_by_coordinates(lat, lon)
         using the GPS coordinates always present in routeInfo["user_location"]
      3. No city AND no GPS          → ask user to specify a city

    The previous implementation called get_weather_report(city) even when city
    was None, which returned {"error": "MISSING_CITY"} and caused the LLM to
    reply "city not found" for commands like "is it hot outside".
    """
    state         = conversation_store.get_session(session_id=session_id)
    user_location = routeInfo.get("user_location", {})
    coords        = _get_origin_coords(user_location)

    # 1. Try to resolve a city name from NLU / session history
    city = _resolve_city(routeInfo, state)

    if city:
        # Named city path
        weather_data = fetch_weather.get_weather_report(city)

        if "error" in weather_data:
            # City string returned by NLU might be garbled — fall back to GPS
            if coords:
                logger.info(
                    f"weather_action: city='{city}' not found, "
                    f"falling back to GPS {coords}"
                )
                weather_data = fetch_weather.get_weather_by_coordinates(*coords)
            else:
                return {
                    "reply": f"I couldn't find weather data for {city}. "
                             f"Could you check the city name?",
                    "action": "CLARIFY",
                    "data": {"city": city}
                }
    elif coords:
        # No city — use GPS coordinates (covers "is it hot outside", "will it rain")
        weather_data = fetch_weather.get_weather_by_coordinates(*coords)
    else:
        # No city and no GPS — ask for clarification
        return {
            "reply": "Which city would you like the weather for?",
            "action": "CLARIFY",
            "data": {"missing": "city"}
        }

    # Hard error from weather engine after all fallbacks exhausted
    if "error" in weather_data:
        logger.error(f"weather_action: weather engine error — {weather_data}")
        return {
            "reply": "I'm having trouble fetching the weather right now. "
                     "Please try again in a moment.",
            "action": "ERROR",
            "data": weather_data
        }

    # Generate natural-language reply via LLM
    reply_text = generate_response_weather.summarize(weather=weather_data, user_query=text)

    # Persist city so follow-up weather queries ("how about there?") resolve correctly.
    # Use the city name returned by the API (canonical) not the user-typed string.
    resolved_city = weather_data.get("city")
    if resolved_city:
        state.last_location = resolved_city

    return {
        "reply": reply_text,
        "action": "REPLY",
        "data": weather_data
    }