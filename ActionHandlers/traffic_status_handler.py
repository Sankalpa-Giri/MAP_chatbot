# traffic_status_handler.py
import FetchServices.fetch_maps as fetch_maps
from config import EVERYDAYLOCATIONS
import driver_rag
import logging
import conversation_store
from conversation_store import Session

logger = logging.getLogger(__name__)

# ==========================================
# INTERNAL HELPERS
# ==========================================

def _format_traffic_reply(destination: str, data: dict) -> str:
    """
    Builds a traffic-only reply from get_traffic_status() data.
    FIX: 'MEDIUM' key replaced with 'MODERATE' — maps_engine._analyze_route()
    is the source of truth and emits 'MODERATE', never 'MEDIUM'.
    """
    congestion = data.get("congestion", "CLEAR")
    delay = data.get("delay_minutes", 0)

    congestion_map = {
        "CLEAR":    f"Traffic to {destination} is clear. No delays expected.",
        "MODERATE": f"Moderate traffic to {destination}. Expect around {delay} min delay.",
        "HEAVY":    f"Heavy traffic to {destination}. Expect around {delay} min delay.",
    }

    return congestion_map.get(
        congestion,
        f"Traffic to {destination}: {congestion}. Estimated delay: {delay} mins."
    )


def _format_eta_reply(destination: str, data: dict) -> str:
    """Builds an ETA reply using get_traffic_status() output."""
    eta = data.get("eta", "unknown")
    duration = data.get("duration_text", "unknown")
    congestion = data.get("congestion", "CLEAR").capitalize()
    return (
        f"You should reach {destination} by around {eta} "
        f"({duration} with current traffic). "
        f"Traffic is {congestion}."
    )


def _format_distance_reply(destination: str, data: dict) -> str:
    """Builds a distance/duration reply using get_distance_duration() output."""
    distance = data.get("distance_text", "unknown")
    duration = data.get("duration_text", "unknown")
    return f"{destination} is {distance} away — about {duration} without traffic."


def _resolve_destination(routeInfo: dict, state: Session) -> str | None:
    """
    Combines NLU entities, referential logic, and RAG shortcuts.
    Accepts the full routeInfo dict so it can handle is_dependent / follow-up turns.
    """
    entities = routeInfo.get("entities", {})
    is_dependent = routeInfo.get("is_dependent", False)

    # 1. Get raw string (either from current turn or session history)
    destination = entities.get("destination")
    if not destination and is_dependent:
        destination = state.last_location

    # Guard against None and whitespace-only strings
    if not destination or not destination.strip():
        return None

    destination = destination.strip()

    # 2. Resolve shortcut labels (office, gym, home) via RAG
    if destination.lower() in EVERYDAYLOCATIONS:
        try:
            rag_address = driver_rag.retrieve_memory(f"{destination} address")
            if rag_address and "don't know" not in rag_address.lower():
                return rag_address
        except Exception as e:
            logger.error(f"RAG resolution failed for '{destination}': {e}")

    return destination


def _get_origin_string(user_location: dict) -> str | None:
    """Formats coordinates for the Maps API."""
    lat = user_location.get("latitude")
    lon = user_location.get("longitude")
    # Use `is not None` — `if lat and lon` silently fails for 0.0 coordinates
    if lat is not None and lon is not None:
        return f"{lat},{lon}"
    return None


# ==========================================
# ACTION
# ==========================================

def traffic_status_action(routeInfo: dict, text: str, session_id: str) -> dict:
    """
    Unified handler for traffic-related intents:
      - GET_TRAFFIC   → congestion level + delay
      - GET_ETA       → estimated arrival time
      - GET_DISTANCE  → distance + travel time (free-flow)

    Parameters:
        routeInfo  : NLU output (intent, entities, is_dependent, user_location)
        text       : Original user message (reserved for future NLU re-prompting)
        session_id : Active session identifier
    """
    state = conversation_store.get_session(session_id=session_id)
    intent = routeInfo.get("intent", "GET_TRAFFIC")
    user_location = routeInfo.get("user_location", {})

    # 1. Resolve Origin
    origin = _get_origin_string(user_location)
    if not origin:
        return {
            "reply": "I need your GPS location to check traffic.",
            "action": "CLARIFY",
            "data": {"missing": "origin"}
        }

    # 2. Resolve Destination
    destination = _resolve_destination(routeInfo, state)
    if not destination:
        return {
            "reply": "Which destination would you like traffic info for?",
            "action": "CLARIFY",
            "data": {"missing": "destination"}
        }

    try:
        # 3. Dispatch by intent
        if intent == "GET_DISTANCE":
            data = fetch_maps.get_distance_duration(origin=origin, destination=destination)
            if "error" in data:
                raise RuntimeError(data["error"])
            reply = _format_distance_reply(destination, data)
            action_data = {
                "distance_text": data.get("distance_text"),
                "duration_text": data.get("duration_text"),
                "destination": destination
            }

        else:
            # GET_TRAFFIC and GET_ETA both need live traffic data
            data = fetch_maps.get_traffic_status(origin=origin, destination=destination)
            if "error" in data:
                raise RuntimeError(data["error"])

            if intent == "GET_ETA":
                reply = _format_eta_reply(destination, data)
            else:
                # Default: GET_TRAFFIC
                reply = _format_traffic_reply(destination, data)

            action_data = {
                "congestion": data.get("congestion"),
                "delay_minutes": data.get("delay_minutes"),
                "eta": data.get("eta"),
                "destination": destination
            }

        # 4. Persist destination so follow-up turns like "what about traffic there?" can resolve via state.last_location
        resolved_place = data.get("destination") or destination
        state.last_location = resolved_place

        return {
            "reply": reply,
            "action": "REPLY",
            "data": action_data
        }

    except Exception as e:
        logger.error(f"Traffic status error for destination='{destination}': {e}")
        return {
            "reply": f"I couldn't get traffic info for {destination} right now.",
            "action": "ERROR",
            "data": {"error": str(e)}
        }