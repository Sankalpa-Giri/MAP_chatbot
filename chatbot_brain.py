# chatbot_brain.py
import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional

import maps_engine
import weather_engine
import spotify_music
import driver_rag
import conversation_store

logger = logging.getLogger(__name__)

# ==========================================
# LLM CHAIN — UNKNOWN intents via RAG
# ==========================================

_llm = ChatOllama(model="llama3.1:8b", temperature=0.3, num_predict=300)

_general_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful in-car voice assistant for drivers in Bhubaneswar, India.
Answer the user's question using the context provided from the knowledge base.
Be concise, practical, and friendly. Avoid long paragraphs — this is a voice response.
If the context is empty or irrelevant, answer from general knowledge.
Never say you are an AI or mention your model name."""),
    ("human", "Conversation history:\n{history}\n\nContext:\n{rag_context}\n\nQuestion: {user_input}")
])

_general_chain = _general_prompt | _llm | StrOutputParser()

# ==========================================
# REPLY FORMATTERS
# ==========================================

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
        f"{i+1}. {s['instruction']} ({s['distance']})"
        for i, s in enumerate(steps)
    )

    return f"{summary}\n\nDirections:\n{step_lines}"


def _format_traffic_reply(destination: str, primary: dict) -> str:
    """Builds a traffic-only reply from primary route data."""
    congestion = primary.get("congestion", "CLEAR")
    delay = primary.get("delay_minutes", 0)

    congestion_map = {
        "CLEAR":  f"Traffic to {destination} is clear. No delays expected.",
        "MEDIUM": f"Moderate traffic to {destination}. Expect around {delay} min delay.",
        "HEAVY":  f"Heavy traffic to {destination}. Expect around {delay} min delay.",
    }

    return congestion_map.get(
        congestion,
        f"Traffic to {destination}: {congestion}. Estimated delay: {delay} mins."
    )


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
# INTERNAL HELPERS
# ==========================================

def _query_llm(user_text: str, session_id: str) -> dict:
    try:
        session = conversation_store.get_session(session_id)
        history = session.get_history_text()

        rag_result = driver_rag.ask_llm(user_text)

        # Memory op was triggered — return directly
        if isinstance(rag_result, dict) and rag_result.get("action") in ("REPLY", "ERROR", "CLARIFY"):
            return rag_result

        context_str = rag_result.get("reply", "") if isinstance(rag_result, dict) else str(rag_result)

        reply = _general_chain.invoke({
            "history": history or "No prior conversation.",
            "rag_context": context_str,
            "user_input": user_text
        })

        return {"reply": reply, "action": "REPLY", "data": {}}

    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        return {
            "reply": "I'm having trouble connecting to my language model.",
            "action": "ERROR",
            "data": {}
        }


def _resolve_shortcut_location(destination: str) -> str:
    shortcuts = {"home", "office", "college", "gym", "work", "school"}
    if destination.lower() not in shortcuts:
        return destination
    try:
        rag_address = driver_rag.retrieve_memory(f"What is my {destination} address?")
        if rag_address and "I don't know" not in rag_address:
            logger.info(f"Resolved '{destination}' → '{rag_address}' from memory")
            return rag_address
    except Exception as e:
        logger.warning(f"Memory lookup failed for '{destination}': {e}")
    return destination


# ==========================================
# ROUTER
# ==========================================

def get_bot_response(nlu_result: dict, original_text: str, session_id: str = "default", current_location: Optional[str] = None) -> dict:
    intent = nlu_result.get("intent", "UNKNOWN")
    entities = nlu_result.get("entities", {})
    user_location = nlu_result.get("user_location")

    # Resolve origin
    origin = current_location
    if user_location:
        origin = f"{user_location['latitude']},{user_location['longitude']}"
    if not origin:
        origin = "KIIT Campus 4"

    # -------- WEATHER --------
    if intent == "GET_WEATHER":
        location = entities.get("location")
        if not location:
            return {
                "reply": "Which city's weather would you like to know?",
                "action": "CLARIFY",
                "data": {"missing": "location"}
            }
        try:
            weather_data = weather_engine.get_weather_report(location)
            reply = (
                f"In {weather_data['city']}, it's currently {weather_data['temperature_c']} "
                f"degrees Celsius, feels like {weather_data['feels_like_c']}. "
                f"{weather_data['description'].capitalize()}."
            )
            return {"reply": reply, "action": "REPLY", "data": weather_data}
        except Exception as e:
            logger.error(f"Weather engine failed: {e}")
            return {
                "reply": f"I couldn't fetch the weather for {location} right now.",
                "action": "ERROR", "data": {}
            }

    # -------- ROUTE (step-by-step) --------
    elif intent == "GET_ROUTE":
        destination = entities.get("destination")
        if not destination:
            return {
                "reply": "Where would you like to go?",
                "action": "CLARIFY",
                "data": {"missing": "destination"}
            }

        destination = _resolve_shortcut_location(destination)

        try:
            route_data = maps_engine.get_route_data(
                origin=origin,
                destination=destination,
                traffic=False
            )
            primary = route_data.get("primary_route", {})

            # Fetch step-by-step instructions
            steps = maps_engine.get_route_steps(origin=origin, destination=destination)

            reply = _format_route_reply(destination, primary, steps)

            return {
                "reply": reply,
                "action": "NAVIGATION",
                "data": {**route_data, "steps": steps}
            }
        except Exception as e:
            logger.error(f"Maps engine failed: {e}")
            return {
                "reply": f"I couldn't get directions to {destination} right now.",
                "action": "ERROR", "data": {}
            }

    # -------- TRAFFIC ONLY --------
    elif intent == "GET_TRAFFIC":
        destination = entities.get("destination")
        if not destination:
            return {
                "reply": "Which destination would you like traffic info for?",
                "action": "CLARIFY",
                "data": {"missing": "destination"}
            }

        destination = _resolve_shortcut_location(destination)

        try:
            route_data = maps_engine.get_route_data(
                origin=origin,
                destination=destination,
                traffic=True          # request traffic data
            )
            primary = route_data.get("primary_route", {})
            reply = _format_traffic_reply(destination, primary)

            return {
                "reply": reply,
                "action": "REPLY",
                "data": {
                    "congestion": primary.get("congestion"),
                    "delay_minutes": primary.get("delay_minutes"),
                    "destination": destination
                }
            }
        except Exception as e:
            logger.error(f"Maps engine failed: {e}")
            return {
                "reply": f"I couldn't get traffic info for {destination} right now.",
                "action": "ERROR", "data": {}
            }

    # -------- ALTERNATE ROUTES --------
    elif intent == "GET_ALTERNATE_ROUTE":
        destination = entities.get("destination")
        if not destination:
            return {
                "reply": "Which destination would you like alternate routes for?",
                "action": "CLARIFY",
                "data": {"missing": "destination"}
            }

        destination = _resolve_shortcut_location(destination)

        try:
            route_data = maps_engine.get_route_data(
                origin=origin,
                destination=destination,
                traffic=False
            )
            alternates = route_data.get("alternative_routes", [])
            reply = _format_alternate_reply(destination, alternates)

            return {
                "reply": reply,
                "action": "NAVIGATION",
                "data": {"alternative_routes": alternates, "destination": destination}
            }
        except Exception as e:
            logger.error(f"Maps engine failed: {e}")
            return {
                "reply": f"I couldn't get alternate routes to {destination} right now.",
                "action": "ERROR", "data": {}
            }

    # -------- MUSIC --------
    elif intent == "GET_MUSIC":
        song = entities.get("song")
        if not song:
            return {
                "reply": "What would you like to listen to?",
                "action": "CLARIFY",
                "data": {"missing": "song"}
            }
        try:
            track_data = spotify_music.search_track(song)
            if "error" in track_data:
                return {
                    "reply": f"I couldn't find {song} on Spotify.",
                    "action": "ERROR", "data": track_data
                }
            return {
                "reply": f"Playing {track_data['track_name']} by {track_data['artist']}.",
                "action": "SPOTIFY_PLAY",
                "data": track_data
            }
        except Exception as e:
            logger.error(f"Spotify engine failed: {e}")
            return {
                "reply": "I couldn't connect to Spotify right now.",
                "action": "ERROR", "data": {}
            }

    # -------- PHONE --------
    elif intent == "GET_PHONE":
        contact = entities.get("contact")
        if not contact:
            return {
                "reply": "Who would you like to call?",
                "action": "CLARIFY",
                "data": {"missing": "contact"}
            }
        return {
            "reply": f"Calling {contact}.",
            "action": "PHONE_CALL",
            "data": {"contact": contact}
        }

    # -------- UNKNOWN → RAG + LLM --------
    else:
        return _query_llm(original_text, session_id)