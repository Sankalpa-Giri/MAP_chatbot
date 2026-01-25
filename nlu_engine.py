import spacy
from vocabulary import (
    TRAFFIC_TRIGGERS,
    WEATHER_TRIGGERS,
    MUSIC_TRIGGERS,
    PHONE_TRIGGERS
)

nlp = spacy.load("en_core_web_sm")


# ==========================================
# 1. TRIGGER CHECKS
# ==========================================

def _contains_any(text, triggers):
    text = text.lower()
    return any(word in text for word in triggers)


def is_traffic_request(text):
    return _contains_any(text, TRAFFIC_TRIGGERS)


def is_weather_request(text):
    return _contains_any(text, WEATHER_TRIGGERS)


def is_music_request(text):
    return _contains_any(text, MUSIC_TRIGGERS)


def is_phone_request(text):
    return _contains_any(text, PHONE_TRIGGERS)


# ==========================================
# 2. ENTITY EXTRACTION
# ==========================================

def extract_location(text, intent_type):
    text_lower = text.lower()

    if intent_type == "weather" and " in " in text_lower:
        return text_lower.split(" in ", 1)[1].strip(" .?!")

    if intent_type == "traffic" and " to " in text_lower:
        return text_lower.split(" to ", 1)[1].strip(" .?!")

    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC"):
            return ent.text

    return None


def extract_song_name(text):
    text_lower = text.lower()
    for trigger in ("play", "listen to"):
        if trigger in text_lower:
            return text_lower.split(trigger, 1)[1].strip(" .?!")
    return None


# ==========================================
# 3. MAIN NLU CONTROLLER
# ==========================================

def nlu_engine_control(text: str) -> dict:
    assumptions = []

    # -------- WEATHER --------
    if is_weather_request(text):
        location = extract_location(text, "weather")
        if not location:
            location = None
            assumptions.append(f"default_location:{location}")

        return {
            "intent": "GET_WEATHER",
            "entities": {"location": location},
            "confidence": 0.85,
            "assumptions": assumptions
        }

    # -------- TRAFFIC --------
    if is_traffic_request(text):
        destination = extract_location(text, "traffic")

        return {
            "intent": "GET_ROUTE_TRAFFIC",
            "entities": {"destination": destination},
            "confidence": 0.9 if destination else 0.6,
            "assumptions": [] if destination else ["missing_destination"]
        }

    # -------- MUSIC --------
    if is_music_request(text):
        song = extract_song_name(text)

        if song is None:
            return {

            }

        return {
            "intent": "GET_MUSIC",
            "entities": {"song": song},
            "confidence": 0.9 if song else 0.5,
            "assumptions": [] if song else ["missing_song"]
        }

    # -------- UNKNOWN --------
    return {
        "intent": "UNKNOWN",
        "entities": {},
        "confidence": 0.3,
        "assumptions": []
    }
