import spacy
from vocabulary import TRAFFIC_TRIGGERS, WEATHER_TRIGGERS, MUSIC_TRIGGERS, PHONE_TRIGGERS

# Load the AI brain
nlp = spacy.load("en_core_web_sm")

# ==========================================
# 1. TRIGGER CHECKS (The Filters)
# ==========================================
def is_traffic_request(text):
    text = text.lower()
    for word in TRAFFIC_TRIGGERS:
        if word in text:
            return True
    return False

def is_weather_request(text):
    text = text.lower()
    for word in WEATHER_TRIGGERS:
        if word in text:
            return True
    return False

def is_music_request(text):
    text = text.lower()
    for word in MUSIC_TRIGGERS:
        if word in text:
            return True
    return False

def is_phone_request(text):
    text = text.lower()
    for word in PHONE_TRIGGERS:
        if word in text:
            return True
    return False

# ==========================================
# 2. WORDS EXTRACTION (The Search)
# ==========================================

def extract_location(text, intent_type):
    """
    Tries to find a location using AI (spaCy). 
    If that fails, it uses a manual fallback based on the intent.
    """
    # A. Manual Fallback
    text_lower = text.lower()
    
    # If looking for weather, we usually say "Weather IN [City]"
    if intent_type == "weather":
        if " in " in text_lower:
            return text_lower.split(" in ", 1)[1].strip(" .?!")

    # If looking for traffic, we usually say "Go TO [City]"
    
    if intent_type == "traffic":
        if " to " in text_lower:
            # We use split to safely get everything AFTER the word "to"
            return text_lower.split(" to ", 1)[1].strip(" .?!")
            

    doc = nlp(text)
    # B. Try AI Second (It's smartest)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            return ent.text    
    
    return None

def extract_song_name(text):
    """Extraxt the song name based on the keywords play and listen to"""
    text = text.lower()
    triggers = ["play", "listen to"]
    for t in triggers:
        if t in text:
            return text.split(t)[1].strip(" .")
    return None
# ==========================================
# 3. MAIN CONTROLLER (The Brain)
# ==========================================

def nlu_engine_control(text):
    
    # --- PATH A: WEATHER ---
    if is_weather_request(text):
        # We tell the extractor to look for weather context (like "in")
        loc = extract_location(text, intent_type="weather")
        
        # Default to "Bhubaneswar" if no city is found in the sentence
        if not loc:
            print("DEBUG: No city found, defaulting to Bhubaneswar")
            loc = "Bhubaneswar"
            
        return {"intent": "get_weather", "location": loc}
    
    # --- PATH B: TRAFFIC ---
    if is_traffic_request(text):
        # We tell the extractor to look for traffic context (like "to")
        dest = extract_location(text, intent_type="traffic")
        
        # If we still can't find a destination, we can't calculate traffic
        if dest:
            return {"intent": "get_route_traffic", "destination": dest}
        else:
            # We recognized the intent, but missing the entity
            return {"intent": "get_route_traffic", "destination": None}
    
    # --- PATH C: TRAFFIC ---
    if is_music_request(text):
        song = extract_song_name(text)
        if song:
            return {"intent": "get_music", "song": song}
        else:
            return {"intent": "unknown", "text": text}
    
    # --- PATH D: FIND PHONE ---
    if is_phone_request(text):
        text = text.lower()
        if "find" in text or "locate" in text:
            return {"intent": "find_phone"}
        else:
            return {"intent": "unknown"}

    # --- PATH E: UNKNOWN ---
    return {"intent": "unknown", "destination": None}

# ==========================================
# 4. TEST ZONE
# ==========================================
if __name__ == "__main__":
    print("-" * 30)
    # Test Traffic (AI should catch 'Jaydev Vihar')
    print(f"Test 1: {nlu_engine_control('Drive me to Jaydev Vihar.')}")
    print("-" * 30)

    # Test Weather (Fallback should catch 'Bhubaneshwar' via 'in')
    print(f"Test 2: {nlu_engine_control('How is the weather in Bhubaneshwar')}")
    print("-" * 30)
    
    # Test Music
    print(f"Test 3: {nlu_engine_control('Play tum hi ho by arijit singh')}")
    print("-" * 30)

    # Test Phone Pushbullet
    print(f"Test 4: {nlu_engine_control('locate my Phone')}")
    print("-" * 30)
