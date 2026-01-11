import googlemaps
from datetime import datetime
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Path to Google Maps API key
API_KEYS_DIR = BASE_DIR / "API_Keys"
API_KEYS_DIR.mkdir(exist_ok=True)

MAPS_KEY_FILE = API_KEYS_DIR / "maps.txt"
if not MAPS_KEY_FILE.exists():
    with open(MAPS_KEY_FILE, "w") as f:
        f.write("FAKE_MAPS_KEY")
    print(f"⚠️ Google Maps API key missing. Created fake key at {MAPS_KEY_FILE}")

with open(MAPS_KEY_FILE, "r") as f:
    MAPS_API_KEY = f.read().strip()

if not MAPS_API_KEY:
    MAPS_API_KEY = "FAKE_MAPS_KEY"

# Initialize Google Maps client
gmaps = googlemaps.Client(key=MAPS_API_KEY)

# ===== ENGINE FUNCTIONS =====

def get_maps_data(origin, destination):
    """
    Fetches raw route and traffic data.
    Returns a list of potential routes.
    """
    try:
        directions = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=datetime.now(),
            alternatives=True
        )
        return directions
    except Exception as e:
        print(f"Maps API Error: {e}")
        return None

def process_traffic_logic(directions):
    """
    Analyzes the raw data to determine congestion levels.
    """
    if not directions:
        return None

    route = directions[0]
    leg = route['legs'][0]

    normal_sec = leg['duration']['value']
    traffic_sec = leg.get('duration_in_traffic', {}).get('value', normal_sec)
    congestion_ratio = traffic_sec / normal_sec

    if congestion_ratio <= 1.15:
        status = "Clear"
    elif 1.15 < congestion_ratio <= 1.4:
        status = "Moderate"
    else:
        status = "Heavy"

    return {
        "summary": route['summary'],
        "distance": leg['distance']['text'],
        "duration": leg.get('duration_in_traffic', {}).get('text', leg['duration']['text']),
        "congestion": status,
        "delay_mins": int((traffic_sec - normal_sec) / 60),
        "destination": leg['end_address'].split(',')[0]
    }

def handle_assistant_command(origin, destination, is_traffic_query=False):
    """
    The main interface for your Chatbot.
    """
    raw_data = get_maps_data(origin, destination)
    analysis = process_traffic_logic(raw_data)

    if not analysis:
        return "I'm sorry, I couldn't find any route information for that location."

    # Direct navigation
    if not is_traffic_query:
        return (f"Navigating to {analysis['destination']} via {analysis['summary']}. "
                f"It is {analysis['distance']} away and will take {analysis['duration']}.")

    # Traffic status
    alt_text = ""
    if len(raw_data) > 1:
        alt_route = raw_data[1]['summary']
        alt_text = f" You might consider taking {alt_route} instead."

    if analysis['congestion'] == "Clear":
        return f"Traffic is clear on {analysis['summary']}. You should reach in {analysis['duration']}."
    else:
        return (f"There is {analysis['congestion']} traffic on {analysis['summary']}. "
                f"Expect a {analysis['delay_mins']} minute delay.{alt_text}")

# Test
if __name__ == "__main__":
    print("--- Navigation Example ---")
    print(handle_assistant_command("KIIT Campus 4", "Jaydev Vihar", is_traffic_query=False))
    print("\n--- Traffic Example ---")
    print(handle_assistant_command("KIIT Campus 4", "Jaydev Vihar road", is_traffic_query=True))
