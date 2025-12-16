# vocabulary.py

# You can organize them by category to keep it readable
ODISHA_LOCATIONS = [
    "Patia", "Bhubaneswar", "Cuttack", "Puri", "KIIT", "Odisha",
    "Chandrasekharpur", "Jaydev Vihar", "Master Canteen", "Rasulgarh",
    "Khandagiri", "Udayagiri", "Lingaraj Temple", "Nandan Kanan",
    "Infocity", "Trident", "Magnet Square", "Nandankanan Zoological Park",
    "Rajarani Temple", "Mukteswara Temple", "Parasurameswara Temple",
    "Shanti Stupa (Dhauli Hills)", "Odisha State Museum",
    "Museum of Tribal Arts & Artefacts", "Bindu Sarovar",
    "Shri Ram Mandir", "ISKCON Temple",
    "Brahmeswara Temple", "Baitala Deula",
    "Ananta Vasudeva Temple", "Kedar Gauri Temple",
    "Pathani Samanta Planetarium", "Ekamra Kanan Botanical Garden",
    "Nicco Park", "Regional Museum of Natural History",
    "Kalinga Stadium", "Biju Patnaik Park (Forest Park)", "Nexus Esplanade", "Baleshwar", "Kalpana Square"
]

COMMON_COMMANDS = [
    "Terminate the program", "Stop listening", "Shut down",
    "Check traffic", "Find route"
]

TRAFFIC_TRIGGERS = [
    # 1. Direct Action Verbs
    "go to", "drive to", "take me to", "ride to", "navigate to",
    "travel to", "head to", "heading to", "move to", "start for","drive me",

    # 2. Traffic & Road Conditions
    "traffic", "congestion", "road block", "jam", "rush",
    "road condition", "is the road clear", "how is the road",
    "heavy traffic", "light traffic",

    # 3. Route & Path Finding
    "route", "directions", "way to", "path to", "best way",
    "shortest way", "fastest way", "alternative route",
    "navigation", "gps", "map to",

    # 4. Time & Distance Queries (Contextual)
    "how long to", "time to reach", "eta for", "distance to",
    "how far is", "travel time", "drive time", "reach",
    
    # 5. Colloquial / Casual (Indian English nuances included) 
    "any rush", "getting to", "show me the way", "guide me to"
]

WEATHER_TRIGGERS = [
    "weather", "temperature", "how hot", "how cold", 
    "rain", "sunny", "forecast", "climate", "degrees"
]

MUSIC_TRIGGERS = [
    "play", "song", "music", "listen to", "start playing"
]

PHONE_TRIGGERS = ["find my phone", "where is my phone", "ping my phone", "send to phone", "locate my phone"]

# Combine them into one master list for Google
# Google accepts a single flat list of strings
MASTER_PHRASE_HINTS = ODISHA_LOCATIONS + COMMON_COMMANDS + WEATHER_TRIGGERS + MUSIC_TRIGGERS