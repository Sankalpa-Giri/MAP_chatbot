import FetchServices.fetch_maps as fetch_maps
import conversation_store
from conversation_store import Session
from config import EVERYDAYLOCATIONS
import driver_rag
import logging

logger = logging.getLogger(__name__)

# ==========================================
# INTERNAL HELPERS
# ==========================================

def _resolve_destination(routeInfo: dict, state: Session) -> str | None:
    """Combines NLU entities, referential logic, and RAG shortcuts."""
    entities = routeInfo.get("entities", {})
    is_dependent = routeInfo.get("is_dependent", False)

    # 1. Get raw string (either from current turn or history)
    destination = entities.get("destination")
    if not destination and is_dependent:
        # Session is a dataclass — use attribute access, not dict .get()
        destination = state.last_location

    # guard against None and whitespace-only strings before further processing
    if not destination or not destination.strip():
        return None

    destination = destination.strip()

    # 2. Check if it's a shortcut (office, gym, home)
    if destination.lower() in EVERYDAYLOCATIONS:
        try:
            rag_address = driver_rag.retrieve_memory(f"{destination} address")
            # Ensure RAG actually returned a real address, not a "not found" string
            if rag_address and "don't know" not in rag_address.lower():
                return rag_address
        except Exception as e:
            logger.error(f"RAG resolution failed for '{destination}': {e}")
            # Fall through and return the raw shortcut word so the caller
            # can still attempt resolution or ask for clarification

    return destination


def _get_origin_string(user_location: dict) -> str | None:
    """Formats coordinates for the Maps API."""
    lat = user_location.get("latitude")
    lon = user_location.get("longitude")

    # `if lat and lon` evaluates to False when either value is 0.0
    # (e.g. a point on the equator or prime meridian — valid coordinates).
    # Use `is not None` to correctly handle zero values.
    if lat is not None and lon is not None:
        return f"{lat},{lon}"
    return None


def _format_route_reply(destination: str, primary: dict, steps: list[dict]) -> str:
    """Builds a full route reply: summary + turn-by-turn steps."""
    congestion = primary.get("congestion", "CLEAR").capitalize()
    delay = primary.get("delay_minutes", 0)
    delay_text = f" with {delay} min delay" if delay > 0 else ""

    summary = (
        f"Route to {destination} via {primary['summary']}. "
        f"{primary['distance_text']}, about {primary['duration_text']}{delay_text}. "
        f"Traffic is {congestion}."
    )

    if not steps:
        return summary

    step_lines = "\n".join(
        f"{i + 1}. {s['instruction']} ({s['distance']})"
        for i, s in enumerate(steps)
    )

    return f"{summary}\n\nDirections:\n{step_lines}"


def _format_alternate_reply(destination: str, alternates: list[dict]) -> str:
    """Builds alternate routes reply."""
    if not alternates:
        return f"No alternate routes found to {destination}."

    lines = [f"Alternate routes to {destination}:"]
    for i, route in enumerate(alternates, 1):
        delay = route.get("delay_minutes", 0)
        delay_text = f", {delay} min delay" if delay > 0 else ", no delay"
        congestion = route.get("congestion", "CLEAR").capitalize()
        lines.append(
            f"{i}. Via {route['summary']} — "
            f"{route['distance_text']}, {route['duration_text']}"
            f"{delay_text}. Traffic: {congestion}."
        )

    return "\n".join(lines)


# ==========================================
# ACTIONS
# ==========================================

def navigation_action(routeInfo: dict, session_id: str) -> dict:
    """
    Unified handler for GET_ROUTE and GET_ALTERNATE_ROUTE.

    Parameters:
        routeInfo  : Output from NLU (intent, entities, is_dependent, user_location)
        session_id : Active session identifier used to load and persist state
    """
    state = conversation_store.get_session(session_id=session_id)
    intent = routeInfo.get("intent", "GET_ROUTE")
    user_location = routeInfo.get("user_location", {})

    # 1. Resolve Origin
    origin = _get_origin_string(user_location)
    if not origin:
        return {
            "reply": "I need your GPS location to provide directions.",
            "action": "CLARIFY",
            "data": {"missing": "origin"}
        }

    # 2. Resolve Destination (handles pronouns like 'there', shortcuts like 'office'/'gym')
    destination = _resolve_destination(routeInfo, state)
    if not destination:
        return {
            "reply": "Where would you like to go?",
            "action": "CLARIFY",
            "data": {"missing": "destination"}
        }

    try:
        # 3. Call Maps Engine
        # traffic=True because users expect real-time conditions for navigation
        route_data = fetch_maps.get_route_data(
            origin=origin, destination=destination, traffic=True
        )

        # 4. Handle based on Intent
        if intent == "GET_ALTERNATE_ROUTE":
            alternates = route_data.get("alternative_routes", [])
            reply = _format_alternate_reply(destination, alternates)
            action_data = {"alternative_routes": alternates}
        else:
            # Standard route + turn-by-turn steps
            primary = route_data.get("primary_route", {})
            steps = fetch_maps.get_route_steps(origin=origin, destination=destination)
            reply = _format_route_reply(destination, primary, steps)
            action_data = {**route_data, "steps": steps}

        # 5. Persist updated state so the user can refer to this location in next turn
        resolved_end = primary.get("destination") if intent != "GET_ALTERNATE_ROUTE" else destination
        state.last_location = resolved_end or destination

        return {
            "reply": reply,
            "action": "NAVIGATION",
            "data": action_data
        }

    except Exception as e:
        logger.error(f"Navigation error for destination='{destination}': {e}")
        return {
            "reply": "I'm having trouble connecting to the maps service right now.",
            "action": "ERROR",
            "data": {"error": str(e)}
        }