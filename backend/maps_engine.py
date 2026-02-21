# maps_engine.py - Google Maps Integration with Embedding-based Place Search

import googlemaps
import re
import chromadb
from datetime import datetime
from pathlib import Path
from backend.config import *
from backend.vocabulary import BHUBANESWAR_KNOWN_PLACES  # ← single source of truth

# ==========================================
# LOAD API KEY
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
API_KEY_PATH = BASE_DIR / "API Keys" / "maps_key.txt"

if not API_KEY_PATH.exists():
    raise RuntimeError(f"Google Maps API key not found at '{API_KEY_PATH}'")

API_KEY = API_KEY_PATH.read_text(encoding="utf-8").strip()
gmaps = googlemaps.Client(key=API_KEY)

# ==========================================
# CHROMADB — cosine similarity place index
# Seeded from vocabulary.BHUBANESWAR_KNOWN_PLACES
# ==========================================

_chroma_client     = chromadb.PersistentClient(path=str(BASE_DIR / "embeddings_data"))
_places_collection = _chroma_client.get_or_create_collection(
    name="bhubaneswar_places",
    metadata={"hnsw:space": "cosine"}
)

def _bootstrap_places():
    """
    Sync ChromaDB with vocabulary.BHUBANESWAR_KNOWN_PLACES.
    - Adds new entries
    - Skips existing ones (no duplicates)
    To add a place: just edit vocabulary.py and restart the server.
    """
    existing     = _places_collection.get()
    existing_ids = set(existing.get("ids", []))

    to_add_ids  = []
    to_add_docs = []
    to_add_meta = []

    for place_id, canonical_name in BHUBANESWAR_KNOWN_PLACES.items():
        if place_id not in existing_ids:
            to_add_ids.append(place_id)
            to_add_docs.append(canonical_name)
            to_add_meta.append({"canonical": canonical_name})

    if to_add_ids:
        _places_collection.add(
            ids=to_add_ids,
            documents=to_add_docs,
            metadatas=to_add_meta
        )
        print(f"🗺️  Seeded {len(to_add_ids)} new places into embedding index")
    else:
        print("🗺️  Places index up to date")

_bootstrap_places()

COSINE_DISTANCE_THRESHOLD = 0.25  # 0 = identical, 2 = opposite — tune if needed

def find_by_embedding(query: str) -> str | None:
    """
    Cosine similarity search against known Bhubaneswar places.
    Returns canonical name if confident, else None → falls through to Google.
    """
    try:
        results   = _places_collection.query(
            query_texts=[query],
            n_results=1,
            include=["documents", "distances"]
        )
        docs      = results.get("documents", [[]])[0]
        distances = results.get("distances",  [[]])[0]

        if not docs or not distances:
            return None

        best_doc, best_dist = docs[0], distances[0]
        print(f"   🔍 Embedding: '{query}' → '{best_doc}' (dist: {best_dist:.3f})")

        if best_dist < COSINE_DISTANCE_THRESHOLD:
            print(f"   ✅ Match accepted: {best_doc}")
            return best_doc

        print(f"   ❌ No confident match (dist {best_dist:.3f} > threshold {COSINE_DISTANCE_THRESHOLD})")
        return None

    except Exception as e:
        print(f"   ⚠️ Embedding error: {e}")
        return None

# ==========================================
# HELPERS
# ==========================================

def clean_name_for_tts(name: str) -> str:
    for part in name.split(","):
        part = part.strip()
        if re.match(r'^[a-zA-Z0-9\s\-\'()&.]+$', part):
            return part
    return name.split(",")[0].strip()

def clean_step(instruction: str) -> str:
    text = re.sub(r'<.*?>', ' ', instruction)
    text = text.replace('&nbsp;', ' ').replace('&amp;', 'and') \
               .replace('&#39;', "'").replace('&quot;', '"')
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'Pass by [^.]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Destination will be on the (left|right)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\w[\w\s]+)\s*/\s*\w[\w\s]+\s*-\s*\1', r'\1', text)
    return ' '.join(text.split()).strip()

def is_key_step(instruction: str) -> bool:
    lower = instruction.lower()
    if any(k in lower for k in ['turn', 'exit', 'merge', 'head', 'take the', 'roundabout', 'u-turn', 'ramp']):
        return True
    if any(k in lower for k in ['continue', 'keep', 'pass by', 'destination']):
        return False
    return True

def is_outside_odisha(location_name: str) -> bool:
    return any(k in location_name.lower() for k in OUTSIDE_ODISHA)

# ==========================================
# FIND PLACE
# Layer 1 → Cosine similarity (vocabulary.py → ChromaDB)
# Layer 2 → Google Places API
# Layer 3 → Geocode fallback
# ==========================================

def find_place(query: str, prefer_bhubaneswar: bool = True) -> dict:
    try:
        # Layer 1: cosine similarity
        embedding_match = find_by_embedding(query)
        search_query = embedding_match if embedding_match else (
            f"{query}, Bhubaneswar, Odisha" if prefer_bhubaneswar else query
        )

        # Layer 2: Google Places API
        try:
            result = gmaps.find_place(
                input=search_query,
                input_type="textquery",
                fields=["name", "geometry", "formatted_address"],
                language="en"
            )
            if result.get("candidates"):
                c = result["candidates"][0]
                print(f"✅ Places API: {c.get('name')}")
                return {
                    "coords":       c["geometry"]["location"],
                    "name":         clean_name_for_tts(c.get("name", query.title())),
                    "full_address": c.get("formatted_address", search_query)
                }
        except Exception as e:
            print(f"   ⚠️ Places API failed: {e}")

        # Layer 3: Geocode fallback
        results = gmaps.geocode(search_query, region="in", language="en")
        if not results and prefer_bhubaneswar:
            results = gmaps.geocode(query, region="in", language="en")
        if not results:
            return None

        r        = results[0]
        location = r["geometry"]["location"]
        name     = None
        for comp in r.get("address_components", []):
            if any(t in comp["types"] for t in ["point_of_interest", "establishment", "premise", "tourist_attraction"]):
                if not re.match(r'^[A-Z0-9]{4}\+[A-Z0-9]{2,}$', comp["long_name"]):
                    name = comp["long_name"]
                    break
        name = name or query.title()
        print(f"✅ Geocode: {clean_name_for_tts(name)}")
        return {
            "coords":       location,
            "name":         clean_name_for_tts(name),
            "full_address": r["formatted_address"]
        }

    except Exception as e:
        print(f"❌ Error finding '{query}': {e}")
        return None

# ==========================================
# GET ROUTE — picks fastest of up to 3 alternatives
# ==========================================

def get_route_data(origin: str, destination: str, get_steps: bool = False) -> dict:
    try:
        origin_data = find_place(origin, prefer_bhubaneswar=True)
        dest_data   = find_place(destination, prefer_bhubaneswar=not is_outside_odisha(destination))

        if not origin_data:
            return {"error": "ORIGIN_NOT_FOUND",      "message": f"Could not find '{origin}'"}
        if not dest_data:
            return {"error": "DESTINATION_NOT_FOUND", "message": f"Could not find '{destination}'"}

        print(f"🗺️  {origin_data['name']} → {dest_data['name']}")

        directions = gmaps.directions(
            origin=origin_data["coords"],
            destination=dest_data["coords"],
            mode="driving",
            departure_time=datetime.now(),
            alternatives=True,
            traffic_model="best_guess"
        )

        if not directions:
            return {"error": "NO_ROUTE_FOUND"}

        # Pick fastest
        best_route, best_dur = None, float('inf')
        for route in directions:
            leg  = route["legs"][0]
            secs = leg.get("duration_in_traffic", {}).get("value", leg["duration"]["value"])
            print(f"   🛣️  via {route['summary']}: {secs//60} mins")
            if secs < best_dur:
                best_dur, best_route = secs, route

        leg         = best_route["legs"][0]
        normal_sec  = leg["duration"]["value"]
        traffic_sec = leg.get("duration_in_traffic", {}).get("value", normal_sec)
        delay_mins  = (traffic_sec - normal_sec) / 60
        distance_km = leg["distance"]["value"] / 1000
        is_peak     = any(s <= datetime.now().hour <= e for s, e in PEAK_HOURS)

        if delay_mins > TRAFFIC_HEAVY_DELAY_MINS:
            traffic_msg = "Heavy traffic"
        elif delay_mins > TRAFFIC_MODERATE_DELAY_MINS or (is_peak and distance_km < 15):
            traffic_msg = "Moderate traffic"
        else:
            traffic_msg = "Traffic is light"

        result = {
            "origin":           origin_data["name"],
            "destination":      dest_data["name"],
            "route_name":       best_route["summary"],
            "distance":         leg["distance"]["text"],
            "duration":         leg.get("duration_in_traffic", {}).get("text", leg["duration"]["text"]),
            "traffic_desc":     traffic_msg,
            "num_alternatives": len(directions)
        }

        if get_steps:
            result["steps"] = [
                clean_step(s["html_instructions"])
                for s in leg["steps"]
                if is_key_step(clean_step(s["html_instructions"]))
                and len(clean_step(s["html_instructions"])) > 5
            ]

        return result

    except Exception as e:
        print(f"❌ Maps error: {e}")
        return {"error": "ERROR", "details": str(e)}