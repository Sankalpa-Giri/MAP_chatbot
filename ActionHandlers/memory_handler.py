import logging
import driver_rag
from config import EVERYDAYLOCATIONS

logger = logging.getLogger(__name__)


def _extract_label(text: str) -> str | None:
    """
    Scans the user's message for a known location label (home, office, gym, etc.).
    Returns the first match, or None if none found.
    Shared by SAVE and UPDATE flows to avoid duplicating the label-extraction logic.
    """
    words = text.lower().split()
    return next((label for label in EVERYDAYLOCATIONS if label in words), None)


def _extract_destination(entities: dict, label: str) -> str | None:
    """
    Returns the destination string from NLU entities.
    Logs a warning if it is missing so callers get a consistent None check.
    """
    destination = entities.get("destination")
    if not destination:
        logger.warning(f"memory_action: no destination entity for label='{label}'")
    return destination


def memory_action(routeInfo: dict, text: str, session_id: str) -> dict:
    """
    Handles memory-related intents: SAVE_ADDRESS, UPDATE_ADDRESS, DELETE_ADDRESS.

    Parameters:
        routeInfo  : NLU output (intent, entities, ...)
        text       : Raw user message — used for label extraction and delete triggers
        session_id : Active session ID (reserved; memory ops are user-global via RAG)
    """
    intent = routeInfo.get("intent")
    entities = routeInfo.get("entities", {})

    # ------------------------------------------------------------------
    if intent == "SAVE_ADDRESS":
        label = _extract_label(text)

        if not label:
            return {
                "reply": "Please specify which address to save (home, office, gym, etc.).",
                "action": "CLARIFY",
                "data": {}
            }

        # FIX: guard missing destination before calling store_memory — without
        # this, store_memory receives location=None, hits its own guard, and
        # returns a reply string that isn't a proper dict, causing a crash on .get()
        destination = _extract_destination(entities, label)
        if not destination:
            return {
                "reply": f"What is the address for your {label}?",
                "action": "CLARIFY",
                "data": {"missing": "destination", "label": label}
            }

        result = driver_rag.store_memory({"label": label, "location": destination})
        return {
            "reply": result.get("reply", "Address saved."),
            "action": result.get("action", "REPLY"),
            "data": result.get("data", {})
        }

    # ------------------------------------------------------------------
    elif intent == "UPDATE_ADDRESS":
        # FIX: was completely empty — implemented using the same label + destination
        # extraction pattern as SAVE_ADDRESS, then delegates to the new
        # driver_rag.update_memory() which checks the entry exists before updating.
        label = _extract_label(text)

        if not label:
            return {
                "reply": "Which address would you like to update? (home, office, gym, etc.)",
                "action": "CLARIFY",
                "data": {}
            }

        destination = _extract_destination(entities, label)
        if not destination:
            return {
                "reply": f"What is the new address for your {label}?",
                "action": "CLARIFY",
                "data": {"missing": "destination", "label": label}
            }

        result = driver_rag.update_memory({"label": label, "location": destination})
        return {
            "reply": result.get("reply", "Address updated."),
            "action": result.get("action", "REPLY"),
            "data": result.get("data", {})
        }

    # ------------------------------------------------------------------
    elif intent == "GET_ADDRESS":
        # User is asking what a saved label resolves to (e.g. "what is my office address")
        # Extract the label from the message, then look it up directly in RAG.
        label = _extract_label(text)

        # Fallback: try the entity from NLU if label scan missed it
        if not label:
            raw_entity = entities.get("destination", "")
            if raw_entity and raw_entity.lower().strip() in EVERYDAYLOCATIONS:
                label = raw_entity.lower().strip()

        if not label:
            return {
                "reply": "Which address would you like to know? (home, office, gym, etc.)",
                "action": "CLARIFY",
                "data": {}
            }

        try:
            address = driver_rag.retrieve_memory(f"{label} address")
            if address and address.strip():
                return {
                    "reply": f"Your {label} is at {address.strip()}.",
                    "action": "REPLY",
                    "data": {"label": label, "address": address.strip()}
                }
            else:
                return {
                    "reply": f"I don't have a {label} address saved yet. You can say 'save my {label} as ...' to add one.",
                    "action": "REPLY",
                    "data": {"label": label}
                }
        except Exception as e:
            logger.error(f"GET_ADDRESS RAG lookup failed for '{label}': {e}")
            return {
                "reply": f"I couldn't retrieve your {label} address right now.",
                "action": "ERROR",
                "data": {}
            }

    # ------------------------------------------------------------------
    elif intent == "DELETE_ADDRESS":
        result = driver_rag.delete_memory(user_text=text)

        # delete_memory returns None if the text didn't start with a trigger word
        # (e.g. "remove my office" — neither "delete" nor "forget" prefix matched)
        if result is None:
            return {
                "reply": "What would you like me to delete from memory?",
                "action": "CLARIFY",
                "data": {}
            }

        return {
            "reply": result.get("reply", "Address deleted."),
            "action": result.get("action", "REPLY"),
            "data": result.get("data", {})
        }

    # ------------------------------------------------------------------
    else:
        logger.warning(f"memory_action: unhandled intent '{intent}'")
        return {
            "reply": "I'm not sure what you'd like me to do with that address.",
            "action": "ERROR",
            "data": {"intent": intent}
        }