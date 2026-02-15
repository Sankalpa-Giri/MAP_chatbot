import spacy
from fuzzywuzzy import fuzz
from textblob import TextBlob
import re

nlp = spacy.load("en_core_web_sm")

SHORTCUTS = {"office": "office", "home": "home", "gym": "gym", "work": "office"}

# ==========================================
# BHUBANESWAR COMMON LOCATIONS (Fast Match)
# ==========================================

COMMON_BHUBANESWAR_PLACES = {
    # Major Areas
    "patia": "Patia, Bhubaneswar",
    "saheed nagar": "Saheed Nagar, Bhubaneswar",
    "jaydev vihar": "Jaydev Vihar, Bhubaneswar",
    "chandrasekharpur": "Chandrasekharpur, Bhubaneswar",
    "khandagiri": "Khandagiri, Bhubaneswar",
    "rasulgarh": "Rasulgarh, Bhubaneswar",
    "nayapalli": "Nayapalli, Bhubaneswar",
    "old town": "Old Town, Bhubaneswar",
    
    # Malls & Shopping
    "esplanade": "Esplanade One Mall",
    "esplanede": "Esplanade One Mall",  # Typo
    "esplanede mall": "Esplanade One Mall",
    "nexus": "Nexus Esplanade",
    "dnk": "DN Regalia Mall",
    "forum mart": "Forum Mart, Bhubaneswar",
    "rupali square": "Rupali Square",
    "rupli square": "Rupali Square",  # Typo
    "rupali squre": "Rupali Square",  # Typo
    "rupli squre": "Rupali Square",  # Typo
    "rupali sqaure": "Rupali Square",  # Typo
    
    # Temples & Tourist Spots
    "lingaraj temple": "Lingaraj Temple",
    "lingaraja temple": "Lingaraj Temple",
    "lingaraj": "Lingaraj Temple",
    "lingaraja mandir": "Lingaraj Temple",
    "rajarani temple": "Rajarani Temple",
    "raja rani temple": "Rajarani Temple",
    "mukteswara temple": "Mukteswara Temple",
    "ram mandir": "Ram Mandir, Bhubaneswar",
    "iskcon": "ISKCON Temple, Bhubaneswar",
    "iskcon temple": "ISKCON Temple, Bhubaneswar",
    "iskcon mandir": "ISKCON Temple, Bhubaneswar",
    "shikhar chandi": "Shikhar Chandi Temple",
    "shikar chandi": "Shikhar Chandi Temple",  # Typo
    "shikhar candi": "Shikhar Chandi Temple",  # Typo
    "shikar candi": "Shikhar Chandi Temple",  # Typo
    "shikar chndi": "Shikhar Chandi Temple",  # Severe typo
    "shikhar chndi": "Shikhar Chandi Temple",  # Severe typo
    "shakhar chandi": "Shikhar Chandi Temple",  # Typo
    "dhauli": "Dhauli Hills",
    "shanti stupa": "Shanti Stupa, Dhauli",
    "udayagiri": "Udayagiri Caves",
    "khandagiri caves": "Khandagiri Caves",
    
    # Parks & Recreation
    "nandankanan": "Nandankanan Zoological Park",
    "nandan kanan": "Nandankanan Zoological Park",
    "nandankanan zoo": "Nandankanan Zoological Park",
    "nandankannan": "Nandankanan Zoological Park",  # Typo
    "nandnkanan": "Nandankanan Zoological Park",  # Typo
    "nandnkanan zoo": "Nandankanan Zoological Park",
    "ekamra kanan": "Ekamra Kanan Botanical Garden",
    "nicco park": "Nicco Park, Bhubaneswar",
    "kalinga stadium": "Kalinga Stadium",
    "kaliga stadium": "Kalinga Stadium",  # Typo
    "kalingha stadium": "Kalinga Stadium",  # Typo
    
    # Educational Institutions
    "kiit": "KIIT University",
    "kiit campus": "KIIT Campus 4",
    "kiit university": "KIIT University",
    "kit road": "KIIT Road",
    "kiit road": "KIIT Road",
    "keet": "KIIT University",  # Typo
    "utkal university": "Utkal University",
    "xavier": "Xavier University, Bhubaneswar",
    
    # Hospitals
    "aiims": "AIIMS Bhubaneswar",
    "aiport": "AIIMS Bhubaneswar",  # Common mishearing
    "sum hospital": "SUM Hospital",
    "apollo": "Apollo Hospital, Bhubaneswar",
    
    # Transport & Infrastructure
    "airport": "Biju Patnaik Airport",
    "aiport": "Biju Patnaik Airport",  # Typo
    "railway station": "Bhubaneswar Railway Station",
    "bus stand": "Baramunda Bus Stand",
    "master canteen": "Master Canteen Square",
    "master cantin": "Master Canteen Square",  # Typo
    "master cantean": "Master Canteen Square",  # Typo
    
    # Special Places
    "infocity": "Infocity, Bhubaneswar",
    "kiit square": "KIIT Square",
    "magnet square": "Magnet Square",
    "kalpana square": "Kalpana Square",
    "s planet": "S Planet Mall",
    "trident": "Trident Hotel, Bhubaneswar",
}

# ==========================================
# TRAFFIC/NAVIGATION TRIGGER WORDS
# ==========================================

TRAFFIC_WORDS = [
    "take me", "take to", "go to", "navigate", "drive", "route", 
    "traffic", "way to", "directions", "how to go", 
    "how do i get", "how to reach", "show me the way", "guide me",
    "drive me", "travel to", "get to", "going to", "head to",
    "take us", "how do i go", "which way", "reach", "visit",
    "want to go", "need to go", "planning to go", "headed to",
    "where is", "how far", "distance to", "let's go"
]

MEMORY_SAVE = ["remember", "save", "store", "keep", "add"]
MEMORY_DELETE = ["forget", "delete", "remove", "clear"]

# ==========================================
# FUZZY MATCHING (Bhubaneswar-centric)
# ==========================================

def fuzzy_match_bhubaneswar(user_input: str) -> str:
    """
    Fuzzy match against Bhubaneswar locations
    Returns corrected name if found
    """
    user_lower = user_input.lower().strip()
    
    # Exact match first
    if user_lower in COMMON_BHUBANESWAR_PLACES:
        return COMMON_BHUBANESWAR_PLACES[user_lower]
    
    # Fuzzy matching with lower threshold for better typo handling
    best_match = None
    best_score = 0
    
    for key, value in COMMON_BHUBANESWAR_PLACES.items():
        score = fuzz.ratio(user_lower, key)
        if score > best_score and score >= 65:  # 65% threshold
            best_score = score
            best_match = value
    
    if best_match:
        print(f"   📍 Fuzzy matched: '{user_input}' → '{best_match}' ({best_score}%)")
    
    return best_match

# ==========================================
# AUTO SPELL-CHECK (General locations)
# ==========================================

def auto_spell_correct(text: str) -> str:
    """
    Automatic spell correction using TextBlob
    Works for ANY location worldwide
    """
    try:
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip very short words
            if len(word) <= 2:
                corrected_words.append(word)
                continue
            
            # Skip numbers
            if word.isdigit():
                corrected_words.append(word)
                continue
            
            # Try spell correction
            try:
                blob = TextBlob(word)
                corrected = str(blob.correct())
                
                # Only use if different and looks valid
                if corrected != word and corrected.isalpha():
                    corrected_words.append(corrected)
                    print(f"   🔤 Spell-check: '{word}' → '{corrected}'")
                else:
                    corrected_words.append(word)
            except:
                corrected_words.append(word)
        
        result = " ".join(corrected_words)
        
        if result != text:
            print(f"   ✨ Auto-corrected: '{text}' → '{result}'")
        
        return result
    except Exception as e:
        print(f"   ⚠️ Spell-check error: {e}")
        return text

# ==========================================
# CLEAN LOCATION TEXT
# ==========================================

def clean_location_text(text: str) -> str:
    """Basic cleanup"""
    text_lower = text.lower()
    
    # Remove "campus X" numbers
    text_lower = re.sub(r'campus\s*\d+', 'campus', text_lower)
    
    # Quick fixes
    quick_fixes = {
        "k iit": "kiit",
        "keet": "kiit",
    }
    
    for wrong, right in quick_fixes.items():
        text_lower = text_lower.replace(wrong, right)
    
    return text_lower

# ==========================================
# EXTRACT LOCATION (Hybrid Approach)
# ==========================================

def extract_location(text: str) -> str:
    """
    HYBRID LOCATION EXTRACTION:
    1. Check shortcuts (home/office/gym)
    2. Try fuzzy match (Bhubaneswar locations - FAST)
    3. Try spell-check (general locations - SLOW but works everywhere)
    4. Use spaCy NER
    """
    if not text:
        return None
    
    print(f"   🔍 Extracting location from: '{text}'")
    
    text = clean_location_text(text)
    
    # STEP 1: Check shortcuts
    for shortcut in SHORTCUTS.keys():
        if shortcut in text:
            print(f"   🏠 Shortcut detected: '{shortcut}'")
            return shortcut
    
    # STEP 2: Remove command words
    cleaned = text
    remove_phrases = [
        "take me to", "take to", "take us to", "go to", "navigate to", 
        "drive to", "route to", "how to go to", "how to get to", 
        "show me the way to", "traffic to", "directions to",
        "how do i go to", "how do i get to", "which way to",
        "i want to go to", "i want to reach", "i need to go to",
        "can you take me to", "planning to go to", "headed to",
        "going to", "reach", "visit", "get to", "where is",
        "how far is", "distance to", "tell me about", "let's go to",
        "could you", "please", "hey", "can you"
    ]
    
    for phrase in remove_phrases:
        cleaned = cleaned.replace(phrase, "").strip()
    
    # Remove filler words
    fillers = ["please", "can you", "could you", "tell me", "about", "the", "a", "an", "?", "!"]
    words = cleaned.split()
    meaningful_words = [w for w in words if w.lower() not in fillers and w]
    cleaned = " ".join(meaningful_words).strip()
    
    if not cleaned or len(cleaned) < 2:
        print("   ⚠️ No meaningful location found")
        return None
    
    # STEP 3: Try Bhubaneswar fuzzy match (FAST & ACCURATE)
    fuzzy_result = fuzzy_match_bhubaneswar(cleaned)
    if fuzzy_result:
        return fuzzy_result
    
    # STEP 4: Try spell-check (for general locations)
    print(f"   🔍 Not in Bhubaneswar list, trying spell-check...")
    corrected = auto_spell_correct(cleaned)
    
    # STEP 5: Use spaCy NER on corrected text
    doc = nlp(corrected.title())
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC", "ORG"):
            print(f"   🎯 NER found: '{ent.text}' ({ent.label_})")
            return ent.text
    
    # STEP 6: Return corrected text if valid
    if len(corrected) > 2:
        final = corrected.title()
        print(f"   ✅ Final location: '{final}'")
        return final
    
    print("   ❌ Could not extract location")
    return None

# ==========================================
# CHECK LOCATION INTENT
# ==========================================

def has_location_intent(text: str) -> bool:
    """Detect if user wants navigation/route"""
    text_lower = text.lower()
    
    # Check explicit navigation words
    if any(word in text_lower for word in TRAFFIC_WORDS):
        return True
    
    # Check if spaCy finds a location
    doc = nlp(text)
    has_location = any(ent.label_ in ("GPE", "LOC", "FAC", "ORG") for ent in doc.ents)
    
    # Check movement/query indicators
    movement_indicators = [
        "want", "need", "looking for", "trying to", "planning",
        "can you", "could you", "tell me", "show me", "where",
        "which", "what", "how far", "distance"
    ]
    
    has_movement = any(indicator in text_lower for indicator in movement_indicators)
    
    if has_location and has_movement:
        return True
    
    if "?" in text and has_location:
        return True
    
    return False

# ==========================================
# PARSE INTENT (Main Function)
# ==========================================

def parse_intent(text: str, current_location=None) -> dict:
    """
    Smart intent parser with hybrid spell correction
    Bhubaneswar-centric but works for any location
    """
    if not text:
        return {"intent": "unknown", "text": ""}
    
    text_lower = text.lower().strip()
    
    # STOP COMMAND
    if any(word in text_lower for word in ["stop", "quit", "exit", "terminate", "shutdown", "bye", "goodbye"]):
        return {"intent": "stop"}
    
    # MEMORY OPERATIONS
    if any(word in text_lower for word in MEMORY_SAVE):
        return {"intent": "save_memory", "text": text}
    
    if any(word in text_lower for word in MEMORY_DELETE):
        return {"intent": "delete_memory", "text": text}
    
    # SINGLE-WORD SHORTCUT
    words = text_lower.split()
    if len(words) == 1 and words[0] in SHORTCUTS:
        return {
            "intent": "get_route_traffic",
            "destination": SHORTCUTS[words[0]],
            "wants_directions": False
        }
    
    # FOLLOW-UP REFERENCES
    follow_up_patterns = ["there", "to it", "that place", "same place", "this place"]
    if any(pattern in text_lower for pattern in follow_up_patterns):
        wants_dirs = any(word in text_lower for word in ["how", "direction", "guide", "way", "step"])
        return {
            "intent": "get_route_traffic",
            "destination": None,  # Use last destination
            "wants_directions": wants_dirs
        }
    
    # EXTRACT LOCATION with HYBRID approach
    dest = extract_location(text)
    
    if dest:
        # Check if user wants navigation
        if has_location_intent(text):
            wants_dirs = any(word in text_lower for word in ["how", "direction", "guide", "step", "way"])
            
            return {
                "intent": "get_route_traffic",
                "destination": dest,
                "wants_directions": wants_dirs
            }
    
    # FALLBACK: If we have a destination, assume navigation
    if dest and len(dest) > 2:
        return {
            "intent": "get_route_traffic",
            "destination": dest,
            "wants_directions": False
        }
    
    # UNKNOWN
    return {"intent": "unknown", "text": text}