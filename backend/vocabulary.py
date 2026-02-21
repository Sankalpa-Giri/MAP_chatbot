# vocabulary.py

# ==========================================
# ODISHA LOCATIONS — for STT hints
# ==========================================

ODISHA_LOCATIONS = [
    "Patia", "Bhubaneswar", "Cuttack", "Puri", "KIIT", "Odisha",
    "KIIT Road", "Kit Road", "Chandrasekharpur", "Jaydev Vihar",
    "Master Canteen", "Rasulgarh", "Khandagiri", "Udayagiri",
    "Lingaraj Temple", "Nandan Kanan", "Infocity", "Trident",
    "Magnet Square", "Nandankanan Zoological Park",
    "Rajarani Temple", "Mukteswara Temple", "Parasurameswara Temple",
    "Shanti Stupa (Dhauli Hills)", "Odisha State Museum",
    "Museum of Tribal Arts & Artefacts", "Bindu Sarovar",
    "Shri Ram Mandir", "ISKCON Temple",
    "Brahmeswara Temple", "Baitala Deula",
    "Ananta Vasudeva Temple", "Kedar Gauri Temple",
    "Pathani Samanta Planetarium", "Ekamra Kanan Botanical Garden",
    "Nicco Park", "Regional Museum of Natural History",
    "Kalinga Stadium", "Biju Patnaik Park (Forest Park)",
    "Nexus Esplanade", "Baleshwar", "Kalpana Square"
]

# ==========================================
# BHUBANESWAR KNOWN PLACES
# Used for cosine similarity search in maps_engine.py
# Format: { "slug-id": "Canonical Google Maps name" }
# ── To add a new place: just add a line here ──
# maps_engine will auto-seed it into ChromaDB on next server start
# ==========================================

BHUBANESWAR_KNOWN_PLACES = {

    # ── Temples ────────────────────────────────────────────────────────────
    "lingaraj-temple":          "Lingaraj Temple, Bhubaneswar",
    "mukteswara-temple":        "Mukteswara Temple, Bhubaneswar",
    "rajarani-temple":          "Rajarani Temple, Bhubaneswar",
    "brahmeshwar-temple":       "Brahmeshwar Temple, Bhubaneswar",
    "parasurameswara-temple":   "Parasurameswara Temple, Bhubaneswar",
    "kedar-gauri-temple":       "Kedara Gouri Temple, Bhubaneswar",
    "ananta-vasudeva-temple":   "Ananta Vasudeva Temple, Bhubaneswar",
    "iskcon-temple":            "ISKCON Temple, Bhubaneswar",
    "ram-mandir":               "Ram Mandir, Bhubaneswar",
    "shikhar-chandi-temple":    "Shikhar Chandi Temple, Bhubaneswar",
    "baitala-deula":            "Baitala Deula, Bhubaneswar",

    # ── Malls & Shopping ───────────────────────────────────────────────────
    "esplanade-one-mall":       "Esplanade One Mall, Bhubaneswar",
    "nexus-esplanade":          "Nexus Esplanade, Bhubaneswar",
    "s-planet-mall":            "S Planet Mall, Bhubaneswar",
    "forum-mart":               "Forum Mart, Bhubaneswar",

    # ── Parks & Recreation ─────────────────────────────────────────────────
    "nandankanan-zoo":          "Nandankanan Zoological Park, Bhubaneswar",
    "ekamra-kanan":             "Ekamra Kanan Botanical Garden, Bhubaneswar",
    "nicco-park":               "Nicco Park, Bhubaneswar",
    "kalinga-stadium":          "Kalinga Stadium, Bhubaneswar",
    "forest-park":              "Biju Patnaik Park, Bhubaneswar",

    # ── Caves, Hills & History ─────────────────────────────────────────────
    "udayagiri-caves":          "Udayagiri and Khandagiri Caves, Bhubaneswar",
    "khandagiri-caves":         "Khandagiri Caves, Bhubaneswar",
    "dhauli-hills":             "Dhauli Hills, Bhubaneswar",
    "shanti-stupa":             "Shanti Stupa, Dhauli, Bhubaneswar",

    # ── Museums & Culture ──────────────────────────────────────────────────
    "odisha-state-museum":      "Odisha State Museum, Bhubaneswar",
    "tribal-arts-museum":       "Museum of Tribal Arts and Artefacts, Bhubaneswar",
    "natural-history-museum":   "Regional Museum of Natural History, Bhubaneswar",
    "pathani-planetarium":      "Pathani Samanta Planetarium, Bhubaneswar",

    # ── Areas & Squares ────────────────────────────────────────────────────
    "patia":                    "Patia, Bhubaneswar",
    "saheed-nagar":             "Saheed Nagar, Bhubaneswar",
    "jaydev-vihar":             "Jaydev Vihar, Bhubaneswar",
    "chandrasekharpur":         "Chandrasekharpur, Bhubaneswar",
    "khandagiri":               "Khandagiri, Bhubaneswar",
    "rasulgarh":                "Rasulgarh, Bhubaneswar",
    "nayapalli":                "Nayapalli, Bhubaneswar",
    "old-town":                 "Old Town, Bhubaneswar",
    "infocity":                 "Infocity, Bhubaneswar",
    "kalpana-square":           "Kalpana Square, Bhubaneswar",
    "master-canteen-square":    "Master Canteen Square, Bhubaneswar",
    "kiit-square":              "KIIT Square, Bhubaneswar",
    "rupali-square":            "Rupali Square, Bhubaneswar",
    "magnet-square":            "Magnet Square, Bhubaneswar",
    "bindu-sagar":              "Bindu Sagar Lake, Bhubaneswar",

    # ── Transport ──────────────────────────────────────────────────────────
    "airport":                  "Biju Patnaik International Airport, Bhubaneswar",
    "railway-station":          "Bhubaneswar Railway Station",
    "baramunda-bus-stand":      "Baramunda Bus Stand, Bhubaneswar",

    # ── Education ──────────────────────────────────────────────────────────
    "kiit-university":          "KIIT University, Bhubaneswar",
    "utkal-university":         "Utkal University, Bhubaneswar",
    "xavier-university":        "Xavier University, Bhubaneswar",

    # ── Hospitals ──────────────────────────────────────────────────────────
    "aiims-bhubaneswar":        "AIIMS Bhubaneswar",
    "sum-hospital":             "SUM Hospital, Bhubaneswar",
    "apollo-hospital":          "Apollo Hospital, Bhubaneswar",
}

# ==========================================
# COMMANDS & TRIGGERS
# ==========================================

COMMON_COMMANDS = [
    "Terminate the program", "Stop listening", "Shut down",
    "Check traffic", "Find route"
]

TRAFFIC_TRIGGERS = [
    # 1. Direct Action Verbs
    "go to", "drive to", "take me to", "ride to", "navigate to",
    "travel to", "head to", "heading to", "move to", "start for", "drive me",

    # 2. Traffic & Road Conditions
    "traffic", "congestion", "road block", "jam", "rush",
    "road condition", "is the road clear", "how is the road",
    "heavy traffic", "light traffic",

    # 3. Route & Path Finding
    "route", "directions", "way to", "path to", "best way",
    "shortest way", "fastest way", "alternative route",
    "navigation", "gps", "map to",

    # 4. Time & Distance Queries
    "how long to", "time to reach", "eta for", "distance to",
    "how far is", "travel time", "drive time", "reach",

    # 5. Colloquial / Casual
    "any rush", "getting to", "show me the way", "guide me to"
]

WEATHER_TRIGGERS = [
    "weather", "temperature", "how hot", "how cold",
    "rain", "sunny", "forecast", "climate", "degrees"
]

MUSIC_TRIGGERS = [
    "play", "song", "music", "listen to", "start playing"
]

PHONE_TRIGGERS = [
    "find my phone", "where is my phone", "ping my phone",
    "send to phone", "locate my phone"
]

# Combine for Google STT phrase hints
MASTER_PHRASE_HINTS = ODISHA_LOCATIONS + COMMON_COMMANDS + WEATHER_TRIGGERS + MUSIC_TRIGGERS