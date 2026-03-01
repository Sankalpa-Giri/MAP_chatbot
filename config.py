# config.py - All Configuration & Keywords in One Place

# ==========================================
# USER SHORTCUTS
# ==========================================

SHORTCUTS = {
    "office": "office",
    "home": "home", 
    "gym": "gym",
    "work": "office"
}

# ==========================================
# BHUBANESWAR COMMON LOCATIONS
# For fast fuzzy matching
# ==========================================

BHUBANESWAR_PLACES = {
    # Major Areas
    "patia": "Patia, Bhubaneswar",
    "saheed nagar": "Saheed Nagar, Bhubaneswar",
    "jaydev vihar": "Jaydev Vihar, Bhubaneswar",
    "chandrasekharpur": "Chandrasekharpur, Bhubaneswar",
    "khandagiri": "Khandagiri, Bhubaneswar",
    "rasulgarh": "Rasulgarh, Bhubaneswar",
    "nayapalli": "Nayapalli, Bhubaneswar",
    "old town": "Old Town, Bhubaneswar",
    "infocity": "Infocity, Bhubaneswar",
    
    # Malls & Shopping
    "esplanade": "Esplanade One Mall",
    "esplanede": "Esplanade One Mall",
    "esplanade mall": "Esplanade One Mall",
    "nexus": "Nexus Esplanade",
    "forum mart": "Forum Mart, Bhubaneswar",
    "rupali square": "Rupali Square",
    "rupli square": "Rupali Square",
    "rupali squre": "Rupali Square",
    "rupli squre": "Rupali Square",
    "s planet": "S Planet Mall",
    
    # Temples & Tourist Spots
    "lingaraj temple": "Lingaraj Temple",
    "lingaraja temple": "Lingaraj Temple",
    "lingaraj": "Lingaraj Temple",
    "rajarani temple": "Rajarani Temple",
    "mukteswara temple": "Mukteswara Temple",
    "ram mandir": "Ram Mandir, Bhubaneswar",
    "iskcon": "ISKCON Temple, Bhubaneswar",
    "iskcon temple": "ISKCON Temple, Bhubaneswar",
    "shikhar chandi": "Shikhar Chandi Temple",
    "shikar chandi": "Shikhar Chandi Temple",
    "shikar chndi": "Shikhar Chandi Temple",
    "dhauli": "Dhauli Hills",
    "shanti stupa": "Shanti Stupa, Dhauli",
    "udayagiri": "Udayagiri Caves",
    "khandagiri caves": "Khandagiri Caves",
    
    # Parks & Recreation
    "nandankanan": "Nandankanan Zoological Park",
    "nandan kanan": "Nandankanan Zoological Park",
    "nandankanan zoo": "Nandankanan Zoological Park",
    "ekamra kanan": "Ekamra Kanan Botanical Garden",
    "nicco park": "Nicco Park, Bhubaneswar",
    "kalinga stadium": "Kalinga Stadium",
    
    # Educational
    "kiit": "KIIT University",
    "kiit campus": "KIIT Campus 4",
    "kiit university": "KIIT University",
    "kiit road": "KIIT Road",
    "keet": "KIIT University",
    "utkal university": "Utkal University",
    "xavier": "Xavier University, Bhubaneswar",
    
    # Hospitals
    "aiims": "AIIMS Bhubaneswar",
    "sum hospital": "SUM Hospital",
    "apollo": "Apollo Hospital, Bhubaneswar",
    
    # Transport
    "airport": "Biju Patnaik Airport",
    "railway station": "Bhubaneswar Railway Station",
    "bus stand": "Baramunda Bus Stand",
    "master canteen": "Master Canteen Square",
    "master cantin": "Master Canteen Square",
    
    # Squares & Landmarks
    "magnet square": "Magnet Square",
    "kalpana square": "Kalpana Square",
    "kiit square": "KIIT Square",
}

# ==========================================
# INTENT KEYWORDS
# ==========================================

# Navigation/Traffic triggers
TRAFFIC_KEYWORDS = [
    "take me", "take to", "go to", "navigate", "drive", "route", 
    "traffic", "way to", "directions", "how to go", 
    "how do i get", "how to reach", "show me the way", "guide me",
    "drive me", "travel to", "get to", "going to", "head to",
    "take us", "how do i go", "which way", "reach", "visit",
    "want to go", "need to go", "planning to go", "headed to",
    "where is", "how far", "distance to", "let's go"
]

# Memory operation keywords
MEMORY_SAVE_KEYWORDS = ["remember", "save", "store", "keep", "add"]
MEMORY_DELETE_KEYWORDS = ["forget", "delete", "remove", "clear"]

# Stop/Exit keywords
STOP_KEYWORDS = ["stop", "quit", "exit", "terminate", "shutdown", "bye", "goodbye"]

# ==========================================
# NLU SETTINGS
# ==========================================

# Fuzzy matching threshold (0-100)
FUZZY_MATCH_THRESHOLD = 65

# Spell-check settings
ENABLE_SPELL_CHECK = True
MIN_WORD_LENGTH_FOR_SPELL_CHECK = 3

# ==========================================
# MAPS API SETTINGS
# ==========================================

# Cities outside Odisha (for better search)
OUTSIDE_ODISHA = [
    "delhi", "mumbai", "bangalore", "kolkata", "chennai", "pune",
    "hyderabad", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "agra", "taj mahal", "india gate", "gateway of india",
    "connaught place", "marine drive"
]

# Traffic thresholds
TRAFFIC_HEAVY_DELAY_MINS = 8
TRAFFIC_MODERATE_DELAY_MINS = 3
PEAK_HOURS = [(9, 11), (17, 20)]  # (start, end) tuples