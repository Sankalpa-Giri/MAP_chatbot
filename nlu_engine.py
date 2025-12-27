import spacy
from vocabulary import TRAFFIC_TRIGGERS, WEATHER_TRIGGERS, MUSIC_TRIGGERS, PHONE_TRIGGERS, ODISHA_LOCATIONS

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
# 2. LOCATION EXTRACTION (Enhanced)
# ==========================================

def find_location_in_vocabulary(text):
    """
    Check if any known location from vocabulary exists in the text.
    Returns the location if found, else None.
    """
    text_lower = text.lower()
    # Sort by length (longest first) to match "KIIT University" before "KIIT"
    sorted_locations = sorted(ODISHA_LOCATIONS, key=len, reverse=True)
    
    for location in sorted_locations:
        if location.lower() in text_lower:
            return location
    return None

def extract_location(text, intent_type):
    """
    Tries multiple strategies to find a location:
    1. Manual keyword extraction (to/in/from)
    2. Known vocabulary matching
    3. spaCy NER as fallback
    """
    text_lower = text.lower()
    
    # Strategy 1: Manual keyword extraction
    if intent_type == "weather":
        # Weather: "weather in [City]"
        if " in " in text_lower:
            parts = text_lower.split(" in ", 1)
            if len(parts) > 1:
                potential_loc = parts[1].strip(" .?!,")
                # Check if it's in vocabulary first
                vocab_match = find_location_in_vocabulary(potential_loc)
                if vocab_match:
                    return vocab_match
                return potential_loc.title()  # Capitalize properly

    if intent_type == "traffic":
        # Traffic: "go to [City]" or "from [City] to [City]"
        
        # Handle "from X to Y" pattern
        if " from " in text_lower and " to " in text_lower:
            # Extract both origin and destination
            from_idx = text_lower.find(" from ")
            to_idx = text_lower.find(" to ")
            
            if from_idx < to_idx:
                # "from X to Y" pattern
                origin_part = text_lower[from_idx + 6:to_idx].strip(" .?!,")
                dest_part = text_lower[to_idx + 4:].strip(" .?!,")
                
                # Check vocabulary for both
                origin = find_location_in_vocabulary(origin_part) or origin_part.title()
                destination = find_location_in_vocabulary(dest_part) or dest_part.title()
                
                return {"origin": origin, "destination": destination}
        
        # Handle "to [City]" pattern (destination only)
        if " to " in text_lower:
            parts = text_lower.split(" to ", 1)
            if len(parts) > 1:
                potential_loc = parts[1].strip(" .?!,")
                vocab_match = find_location_in_vocabulary(potential_loc)
                if vocab_match:
                    return vocab_match
                return potential_loc.title()
    
    # Strategy 2: Check known vocabulary
    vocab_match = find_location_in_vocabulary(text)
    if vocab_match:
        print(f"DEBUG: Found location in vocabulary: {vocab_match}")
        return vocab_match
    
    # Strategy 3: Use spaCy NER as last resort
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            print(f"DEBUG: spaCy found location: {ent.text}")
            # Check if spaCy result matches vocabulary
            vocab_match = find_location_in_vocabulary(ent.text)
            if vocab_match:
                return vocab_match
            return ent.text
    
    return None

def extract_song_name(text):
    """Extract the song name based on the keywords play and listen to"""
    text = text.lower()
    triggers = ["play", "listen to"]
    for t in triggers:
        if t in text:
            song_part = text.split(t, 1)[1].strip(" .")
            # Remove common words at the end
            for end_word in ["please", "now", "song"]:
                if song_part.endswith(end_word):
                    song_part = song_part[:-len(end_word)].strip()
            return song_part
    return None

# ==========================================
# 3. MAIN CONTROLLER (The Brain)
# ==========================================

def nlu_engine_control(text):
    
    # --- PATH A: WEATHER ---
    if is_weather_request(text):
        loc = extract_location(text, intent_type="weather")
        
        # Default to "Bhubaneswar" if no city is found
        if not loc:
            print("DEBUG: No city found, defaulting to Bhubaneswar")
            loc = "Bhubaneswar"
            
        return {"intent": "get_weather", "location": loc}
    
    # --- PATH B: TRAFFIC ---
    if is_traffic_request(text):
        location_result = extract_location(text, intent_type="traffic")
        
        # Check if we got origin and destination (dict) or just destination (string)
        if isinstance(location_result, dict):
            return {
                "intent": "get_route_traffic",
                "origin": location_result.get("origin"),
                "destination": location_result.get("destination")
            }
        elif location_result:
            return {
                "intent": "get_route_traffic",
                "origin": None,  # Will use default
                "destination": location_result
            }
        else:
            # Recognized intent but missing location
            return {
                "intent": "get_route_traffic",
                "origin": None,
                "destination": None
            }
    
    # --- PATH C: MUSIC ---
    if is_music_request(text):
        song = extract_song_name(text)
        if song:
            return {"intent": "get_music", "song": song}
        else:
            return {"intent": "get_music", "song": None}
    
    # --- PATH D: FIND PHONE ---
    if is_phone_request(text):
        return {"intent": "find_phone"}

    # --- PATH E: UNKNOWN ---
    return {"intent": "unknown", "text": text}

# ==========================================
# 4. TEST ZONE
# ==========================================
if __name__ == "__main__":
    print("-" * 50)
    
    # Test 1: Simple destination
    test1 = 'Drive me to Jaydev Vihar'
    print(f"Test 1: {test1}")
    print(f"Result: {nlu_engine_control(test1)}")
    print("-" * 50)

    # Test 2: Weather with location in vocabulary
    test2 = 'How is the weather in Bhubaneswar'
    print(f"Test 2: {test2}")
    print(f"Result: {nlu_engine_control(test2)}")
    print("-" * 50)
    
    # Test 3: From-To pattern
    test3 = 'Navigate from Master Canteen to KIIT'
    print(f"Test 3: {test3}")
    print(f"Result: {nlu_engine_control(test3)}")
    print("-" * 50)
    
    # Test 4: Music
    test4 = 'Play tum hi ho by arijit singh'
    print(f"Test 4: {test4}")
    print(f"Result: {nlu_engine_control(test4)}")
    print("-" * 50)

    # Test 5: Phone location
    test5 = 'locate my Phone'
    print(f"Test 5: {test5}")
    print(f"Result: {nlu_engine_control(test5)}")
    print("-" * 50)
    
    # Test 6: Vocabulary matching
    test6 = 'Traffic to Patia'
    print(f"Test 6: {test6}")
    print(f"Result: {nlu_engine_control(test6)}")
    print("-" * 50)
    
    # Test 7: Complex navigation
    test7 = 'How do I get from Chandrasekharpur to Nandan Kanan'
    print(f"Test 7: {test7}")
    print(f"Result: {nlu_engine_control(test7)}")
    print("-" * 50)
