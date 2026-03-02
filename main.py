'''
    Used for parsing intent, extracting latitude and longitude, get the bot reply and check for correct structure. 
    It orchestrates the request to response process.
'''
import nlu_engine
import chatbot_brain
import conversation_store
from typing import Optional

def handle_user_input(user_text: str,latitude: Optional[float] = None,longitude: Optional[float] = None,session_id: str = "default") -> dict:
    """
    Orchestrates the full request → response pipeline.

    Input:
        user_text : str
        latitude  : float (optional, from mobile GPS)
        longitude : float (optional, from mobile GPS)
        session_id: str 

    Output:
        dict with at minimum {"reply": str}
    """
    try:
        # ── 1. NLU — intent + entity extraction ─────────────────────────────
        analysis_result = nlu_engine.parse_intent(user_text)

        # Attach GPS coordinates if provided by client
        # These are not used by NLU — chatbot_brain uses them for routing
        if latitude is not None and longitude is not None:
            analysis_result["user_location"] = {"latitude": latitude, "longitude": longitude}

        # ── 2. Chatbot brain — generates response based on intent ────────────
        bot_reply = chatbot_brain.get_bot_response(analysis_result, user_text, session_id=session_id)

        # ── 3. Update conversation history ───────────────────────────────────
        session = conversation_store.get_session(session_id)
        resolved_location = (
            analysis_result.get("entities", {}).get("destination") or
            analysis_result.get("entities", {}).get("location")
        )
        session.add_turn(
            role="user",
            text=user_text,
            intent=analysis_result.get("intent"),
            location=resolved_location
        )
        if isinstance(bot_reply, dict):
            session.add_turn(role="assistant", text=bot_reply.get("reply", ""))
        else:
            session.add_turn(role="assistant", text=str(bot_reply))

        # ── 4. Normalize response shape ──────────────────────────────────────
        if isinstance(bot_reply, dict):
            return bot_reply

        return {
            "reply": str(bot_reply),
            "action": "REPLY",
            "metadata": analysis_result
        }

    except Exception as e:
        return {
            "reply": "Something went wrong processing your request.",
            "action": "ERROR",
            "error": str(e)
        }
    
import pprint

if __name__ == "__main__":
    result = handle_user_input(user_text="Whats the weather", latitude=20.353708, longitude=85.819925, session_id='2')
    pprint.pprint(result)