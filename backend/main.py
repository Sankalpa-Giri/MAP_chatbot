import nlu_engine     # Logic
import chatbot_brain  # Brain
import geocoder

g = geocoder.ip("me")
CURRENT_LOCATION = g.latlng

def handle_user_input(user_text: str) -> dict:
    """
    CORE LOGIC (API-safe, stateless)

    Input: user text
    Output: structured response
    """

    if not user_text or not user_text.strip():
        return {
            "reply": "I didn't catch that.",
            "action": "NONE"
        }

    user_text_lower = user_text.lower()

    # 1. Termination intent (API-safe)
    if "terminate" in user_text_lower:
        return {
            "reply": "Shutting down. Goodbye!",
            "action": "TERMINATE"
        }

    # 2. Intent + NLU
    analysis_result = nlu_engine.nlu_engine_control(user_text)

    # 3. LLM reasoning
    bot_reply = chatbot_brain.get_bot_response(analysis_result,user_text,None)

    if isinstance(bot_reply, dict) and "reply" in bot_reply and "action" in bot_reply:
        return bot_reply


    # Fallback
    return {
        "reply": str(bot_reply),
        "action": "UNKNOWN",
        "metadata": analysis_result
    }

