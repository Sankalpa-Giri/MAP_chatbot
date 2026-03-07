'''
Orchestrates the full request → response pipeline.
Diagnostic logging added to every stage so failures are visible
in the uvicorn console output.
'''
import logging
from identify_domain import parse_domain
from identify_intent import parse_intent
from peform_action import perform_action
from typing import Optional

logger = logging.getLogger(__name__)


def handle_user_input(
    user_text: str,
    session_id: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> dict:
    """
    Orchestrates the full request -> response pipeline.

    Input:
        user_text  : str
        session_id : str
        latitude   : float (from mobile GPS)
        longitude  : float (from mobile GPS)

    Output:
        dict with at minimum {"reply": str}
    """
    try:
        # ── 1. Domain ────────────────────────────────────────────────────────
        domain_result = parse_domain(user_text)
        domain = str(domain_result.get("domain", "UNKNOWN"))
        #logger.info(f"[DOMAIN]  text={user_text!r}  →  {domain}")

        # ── 2. Intent ────────────────────────────────────────────────────────
        routeInfo = parse_intent(
            identify_domain=domain_result,
            text=user_text,
            session_id=session_id
        )
        #logger.info(f"[INTENT]  {routeInfo}")

        # ── 3. Attach GPS ─────────────────────────────────────────────────────
        if latitude is not None and longitude is not None:
            routeInfo["user_location"] = {"latitude": latitude, "longitude": longitude}

        #return routeInfo

        # ── 4. Action ─────────────────────────────────────────────────────────
        _reply = perform_action(
            routeInfo=routeInfo,
            domain=domain,
            original_text=user_text,
            session_id=session_id
        )
        logger.info(f"[ACTION]  {_reply}")

        # ── 5. Normalise response shape ───────────────────────────────────────
        if not isinstance(_reply, dict):
            logger.warning(f"[MAIN] perform_action returned non-dict: {type(_reply)} — wrapping")
            return {"reply": str(_reply)}

        # Guard: if the dict exists but has no "reply" key, log and patch
        if "reply" not in _reply or _reply["reply"] is None:
            logger.error(f"[MAIN] perform_action returned dict with no 'reply' key: {_reply}")
            return {
                "reply": "Something went wrong — no reply was generated.",
                "action": "ERROR",
                "data": {"raw": str(_reply)}
            }

        return _reply

    except Exception as e:
        logger.exception(f"[MAIN] Unhandled exception: {e}")
        return {
            "reply": f"Something went wrong processing your request. Error: {e}"
        }


import pprint
if __name__ == "__main__":
    tests = [
        ("is there any traffic on jaydev vihar road", 20.353708, 85.819925),
    ]
    for text, lat, lon in tests:
        print(f"\n{'─'*60}")
        print(f"INPUT: {text!r}")
        result = handle_user_input(user_text=text, latitude=lat, longitude=lon, session_id="test")
        pprint.pprint(result)