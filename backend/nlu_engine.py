# nlu_engine.py - Intent Detection & Location Extraction

import spacy
from fuzzywuzzy import fuzz
from textblob import TextBlob
import re
from backend.config import *

nlp = spacy.load("en_core_web_sm")

# ==========================================
# FUZZY MATCHING
# ==========================================

def fuzzy_match_location(user_input: str) -> str:
    """Match against known Bhubaneswar locations"""
    user_lower = user_input.lower().strip()
    
    # Exact match
    if user_lower in BHUBANESWAR_PLACES:
        return BHUBANESWAR_PLACES[user_lower]
    
    # Fuzzy match
    best_match = None
    best_score = 0
    
    for key, value in BHUBANESWAR_PLACES.items():
        score = fuzz.ratio(user_lower, key)
        if score > best_score and score >= FUZZY_MATCH_THRESHOLD:
            best_score = score
            best_match = value
    
    if best_match:
        print(f"   📍 Matched: '{user_input}' → '{best_match}' ({best_score}%)")
    
    return best_match

# ==========================================
# SPELL CORRECTION
# ==========================================

def spell_correct(text: str) -> str:
    """Auto spell-check for general locations"""
    if not ENABLE_SPELL_CHECK:
        return text
    
    try:
        words = text.split()
        corrected_words = []
        
        for word in words:
            if len(word) <= MIN_WORD_LENGTH_FOR_SPELL_CHECK or word.isdigit():
                corrected_words.append(word)
                continue
            
            try:
                blob = TextBlob(word)
                corrected = str(blob.correct())
                
                if corrected != word and corrected.isalpha():
                    corrected_words.append(corrected)
                    print(f"   🔤 '{word}' → '{corrected}'")
                else:
                    corrected_words.append(word)
            except:
                corrected_words.append(word)
        
        return " ".join(corrected_words)
    except:
        return text

# ==========================================
# LOCATION EXTRACTION
# ==========================================

def extract_location(text: str) -> str:
    """
    Extract location using hybrid approach:
    1. Check shortcuts
    2. Fuzzy match (Bhubaneswar)
    3. Spell-check (general)
    4. spaCy NER
    """
    if not text:
        return None
    
    print(f"   🔍 Extracting from: '{text}'")
    
    # Clean text
    text = text.lower()
    text = re.sub(r'campus\s*\d+', 'campus', text)
    text = text.replace("k iit", "kiit").replace("keet", "kiit")
    
    # Check shortcuts
    for shortcut in SHORTCUTS.keys():
        if shortcut in text:
            print(f"   🏠 Shortcut: '{shortcut}'")
            return shortcut
    
    # Remove command words
    remove_phrases = [
        "take me to", "take to", "go to", "navigate to", "drive to",
        "route to", "how to go to", "how to get to", "traffic to",
        "directions to", "where is", "how far is", "distance to",
        "tell me about", "let's go to", "show me", "guide me",
        "going to", "headed to", "visit", "reach", "get to"
    ]
    
    cleaned = text
    for phrase in remove_phrases:
        cleaned = cleaned.replace(phrase, "").strip()
    
    # Remove fillers
    fillers = ["please", "can you", "could you", "tell me", "about", "the", "a", "an"]
    words = cleaned.split()
    meaningful = [w for w in words if w not in fillers and w]
    cleaned = " ".join(meaningful).strip()
    
    if not cleaned or len(cleaned) < 2:
        return None
    
    # Try Bhubaneswar fuzzy match
    fuzzy_result = fuzzy_match_location(cleaned)
    if fuzzy_result:
        return fuzzy_result
    
    # Try spell-check
    corrected = spell_correct(cleaned)
    
    # Try spaCy NER
    doc = nlp(corrected.title())
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC", "ORG"):
            print(f"   🎯 NER: '{ent.text}'")
            return ent.text
    
    # Return corrected text
    if len(corrected) > 2:
        return corrected.title()
    
    return None

# ==========================================
# INTENT DETECTION
# ==========================================

def has_location_intent(text: str) -> bool:
    """Check if user wants navigation"""
    text_lower = text.lower()
    
    # Check traffic keywords
    if any(word in text_lower for word in TRAFFIC_KEYWORDS):
        return True
    
    # Check location entities
    doc = nlp(text)
    has_location = any(ent.label_ in ("GPE", "LOC", "FAC", "ORG") for ent in doc.ents)
    
    # Check movement words
    movement = ["want", "need", "where", "how far", "distance"]
    has_movement = any(word in text_lower for word in movement)
    
    return has_location and has_movement

def parse_intent(text: str, current_location=None) -> dict:
    """Main intent parser"""
    if not text:
        return {"intent": "unknown", "text": ""}
    
    text_lower = text.lower().strip()
    
    # STOP
    if any(word in text_lower for word in STOP_KEYWORDS):
        return {"intent": "stop"}
    
    # MEMORY SAVE
    if any(word in text_lower for word in MEMORY_SAVE_KEYWORDS):
        return {"intent": "save_memory", "text": text}
    
    # MEMORY DELETE
    if any(word in text_lower for word in MEMORY_DELETE_KEYWORDS):
        return {"intent": "delete_memory", "text": text}
    
    # SHORTCUTS
    words = text_lower.split()
    if len(words) == 1 and words[0] in SHORTCUTS:
        return {
            "intent": "get_route_traffic",
            "destination": SHORTCUTS[words[0]],
            "wants_directions": False
        }
    
    # FOLLOW-UP
    follow_up = ["there", "to it", "that place", "same place"]
    if any(pattern in text_lower for pattern in follow_up):
        wants_dirs = any(word in text_lower for word in ["how", "direction", "guide", "way"])
        return {
            "intent": "get_route_traffic",
            "destination": None,
            "wants_directions": wants_dirs
        }
    
    # LOCATION EXTRACTION
    dest = extract_location(text)
    
    if dest:
        if has_location_intent(text):
            wants_dirs = any(word in text_lower for word in ["how", "direction", "guide", "way"])
            return {
                "intent": "get_route_traffic",
                "destination": dest,
                "wants_directions": wants_dirs
            }
    
    # FALLBACK
    if dest and len(dest) > 2:
        return {
            "intent": "get_route_traffic",
            "destination": dest,
            "wants_directions": False
        }
    
    # UNKNOWN
    return {"intent": "unknown", "text": text}