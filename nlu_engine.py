import spacy
from vocabulary import TRAFFIC_TRIGGERS, WEATHER_TRIGGERS, MUSIC_TRIGGERS, PHONE_TRIGGERS, ODISHA_LOCATIONS

# Load the AI brain
nlp = spacy.load("en_core_web_sm")

# ==========================================
# TRIGGER CHECKS
# ==========================================
def is_traffic_request(text):
    text = text.lower()
    return any(word in text for word in TRAFFIC_TRIGGERS)

def is_weather_request(text):
    text = text.lower()
    return any(word in text for word in WEATHER_TRIGGERS)

def is_music_request(text):
    text = text.lower()
    return any(word in text for word in MUSIC_TRIGGERS)

def is_phone_request(text):
    text = text.lower()
    return any(word in text for word in PHONE_TRIGGERS)

# ==========================================
# LOCATION EXTRACTION
# ==========================================

def find_location_in_vocabulary(text):
    """Check if any known location from vocabulary exists in the text"""
    text_lower = text.lower()
    sorted_locations = sorted(ODISHA_LOCATIONS, key=len, reverse=True)
    
    for location in sorted_locations:
        if location.lower() in text_lower:
            return location
    return None

def extract_location(text, intent_type, current_location=None):
    """
    Extract location using multiple strategies:
    1. Manual keyword extraction (from/to/in)
    2. Vocabulary matching
    3. spaCy NER
    """
    text_lower = text.lower()
    
    # Strategy 1: Manual keyword extraction
    if intent_type == "weather":
        if " in " in text_lower:
            parts = text_lower.split(" in ", 1)
            if len(parts) > 1:
                potential_loc = parts[1].strip(" .?!,")
                vocab_match = find_location_in_vocabulary(potential_loc)
                if vocab_match:
                    return vocab_match
                return potential_loc.title()
    
    if intent_type == "traffic":
        # Handle "from X to Y" pattern
        if " from " in text_lower and " to " in text_lower:
            from_idx = text_lower.find(" from ")
            to_idx = text_lower.find(" to ")
            
            if from_idx < to_idx:
                origin_part = text_lower[from_idx + 6:to_idx].strip(" .?!,")
                dest_part = text_lower[to_idx + 4:].strip(" .?!,")
                
                origin = find_location_in_vocabulary(origin_part) or origin_part.title()
                destination = find_location_in_vocabulary(dest_part) or dest_part.title()
                
                return {"origin": origin, "destination": destination}
        
        # Handle "to [City]" pattern
        if " to " in text_lower:
            parts = text_lower.split(" to ", 1)
            if len(parts) > 1:
                potential_loc = parts[1].strip(" .?!,")
                vocab_match = find_location_in_vocabulary(potential_loc)
                if vocab_match:
                    return vocab_match
                return potential_loc.title()
    
    # Strategy 2: Vocabulary matching
    vocab_match = find_location_in_vocabulary(text)
    if vocab_match:
        print(f"DEBUG: Found in vocabulary: {vocab_match}")
        return vocab_match
    
    # Strategy 3: spaCy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            print(f"DEBUG: spaCy found: {ent.text}")
            vocab_match = find_location_in_vocabulary(ent.text)
            if vocab_match:
                return vocab_match
            return ent.text
    
    return None

def extract_song_name(text):
    """Extract the song name"""
    text_lower = text.lower()
    triggers = ["play", "listen to"]
    
    for trigger in triggers:
        if trigger in text_lower:
            song_part = text_lower.split(trigger, 1)[1].strip(" .!?")
            for end_word in ["please", "now", "song"]:
                if song_part.endswith(end_word):
                    song_part = song_part[:-len(end_word)].strip()
            return song_part
    return None

# ==========================================
# MAIN NLU ENGINE
# ==========================================

def nlu_engine_control(text, current_location=None):
    """
    Main NLU engine
    
    Args:
        text: User's speech input
        current_location: GPS coordinates as (lat, lng) tuple
    
    Returns:
        Dictionary with intent and extracted entities
    """
    
    # Convert GPS to string if needed
    current_loc_str = None
    if current_location:
        if isinstance(current_location, (list, tuple)) and len(current_location) == 2:
            current_loc_str = f"{current_location[0]},{current_location[1]}"
        else:
            current_loc_str = current_location
    
    # --- WEATHER ---
    if is_weather_request(text):
        loc = extract_location(text, "weather", current_loc_str)
        if not loc:
            loc = "Bhubaneswar"
        
        return {
            "intent": "get_weather",
            "location": loc
        }
    
    # --- TRAFFIC ---
    if is_traffic_request(text):
        location_result = extract_location(text, "traffic", current_loc_str)
        
        # Handle dictionary result (origin + destination)
        if isinstance(location_result, dict):
            return {
                "intent": "get_route_traffic",
                "origin": location_result.get("origin"),
                "destination": location_result.get("destination")
            }
        
        # Handle single location (destination only)
        if location_result:
            return {
                "intent": "get_route_traffic",
                "origin": None,
                "destination": location_result
            }
        
        # No location found
        return {
            "intent": "get_route_traffic",
            "origin": None,
            "destination": None
        }
    
    # --- MUSIC ---
    if is_music_request(text):
        song = extract_song_name(text)
        return {
            "intent": "get_music",
            "song": song
        }
    
    # --- PHONE ---
    if is_phone_request(text):
        return {"intent": "find_phone"}
    
    # --- UNKNOWN ---
    return {
        "intent": "unknown",
        "text": text
    }

# ==========================================
# TEST ZONE
# ==========================================

if __name__ == "__main__":
    print("=" * 60)
    print("NLU ENGINE TEST")
    print("=" * 60)
    
    test_cases = [
        "Drive me to Jaydev Vihar",
        "How is the weather in Bhubaneswar",
        "Navigate from Master Canteen to KIIT",
        "Play tum hi ho by arijit singh",
        "Locate my Phone",
        "Traffic to Patia",
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test}'")
        result = nlu_engine_control(test, current_location=(20.2961, 85.8245))
        print(f"Result: {result}")
        print("-" * 60)
