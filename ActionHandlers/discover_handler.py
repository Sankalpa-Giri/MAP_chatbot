# discover_handler.py
import logging
from FetchServices import fetch_maps
import conversation_store

logger = logging.getLogger(__name__)


def _get_origin_string(user_location: dict) -> str | None:
    """Formats coordinates for the Maps API."""
    lat = user_location.get("latitude")
    lon = user_location.get("longitude")
    if lat is not None and lon is not None:
        return f"{lat},{lon}"
    return None


def _format_discover_reply(category: str, places: list[dict]) -> str:
    """
    Builds a natural-language reply listing nearby places.
    The first result is the nearest; subsequent ones give the user options.
    """
    if not places:
        return f"I couldn't find any {category} near you right now."

    top = places[0]
    if len(places) == 1:
        return (
            f"The nearest {category} I found is {top['name']} "
            f"at {top['vicinity']}."
        )

    options = ", ".join(p["name"] for p in places[1:])
    return (
        f"The nearest {category} is {top['name']} at {top['vicinity']}. "
        f"There's also {options} nearby. "
    )


def discover_action(routeInfo: dict, text: str, session_id: str) -> dict:
    """
    Handles FIND_NEARBY intent — discovers nearby places of a category
    and stores the nearest result in session so the follow-up
    "take me there" / "navigate me" works immediately via navigation_handler.

    Flow:
      1. Extract the place category from NLU entity (e.g. "restaurant", "cafe").
      2. Call maps_engine.find_nearby() with rank_by=distance.
      3. Reply with the top 3 nearby results.
      4. Store the nearest resolved address in state.last_location so the
         next navigation turn resolves "there" to the correct place.
    """
    state         = conversation_store.get_session(session_id=session_id)
    user_location = routeInfo.get("user_location", {})
    entities      = routeInfo.get("entities", {})

    # 1. Require GPS — category search is meaningless without coordinates
    origin = _get_origin_string(user_location)
    if not origin:
        return {
            "reply": "I need your GPS location to find nearby places.",
            "action": "CLARIFY",
            "data": {"missing": "origin"}
        }

    # 2. Extract category from NLU entity
    #    The discover prompt always extracts a category word, defaulting to
    #    "restaurant" for vague queries like "take me somewhere nice".
    category = (entities.get("destination") or "restaurant").strip().lower()

    # 3. Find nearby places
    result = fetch_maps.find_nearby(category=category, origin=origin, limit=3)

    if "error" in result:
        logger.error(f"discover_action: find_nearby error — {result}")
        return {
            "reply": f"I couldn't find any {category} near you right now. "
                     f"Try being more specific or check your connection.",
            "action": "ERROR",
            "data": result
        }

    places = result.get("places", [])
    top    = result.get("top", "")

    # 4. Store the nearest resolved address so "take me there" works next turn.
    #    This is the critical step — without it the follow-up navigation
    #    falls back to an old session location or asks "where would you like to go?"
    if top:
        state.last_location = top
        logger.info(f"discover_action: stored last_location='{top}' for session '{session_id}'")

    reply = _format_discover_reply(category, places)

    return {
        "reply": reply,
        "action": "DISCOVER",
        "data": {
            "category":   category,
            "places":     places,
            "navigating_to": top
        }
    }