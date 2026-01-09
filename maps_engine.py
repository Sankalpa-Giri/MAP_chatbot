import googlemaps
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
try:
    with open(r"API Keys\Gemini_api_key.txt", "r") as api_file:
        API_KEY = api_file.read().strip()
except FileNotFoundError:
    print("Error: API Key file not found.")
    API_KEY = None

gmaps = googlemaps.Client(key=API_KEY)

# ==========================================
# 2. THE ENGINE
# ==========================================

def get_maps_data(origin, destination):
    """
    Fetches raw route and traffic data. 
    Returns a list of potential routes.
    """
    try:
        # departure_time="now" is required for traffic data
        # Allows suggesting other routes
        directions = gmaps.directions(origin, destination, mode="driving", departure_time=datetime.now(), alternatives=True)
        return directions
    except Exception as e:
        print(f"Maps API Error: {e}")
        return None

def process_traffic_logic(directions):
    """
    Analyses the raw data to determine congestion levels.
    """
    if not directions:
        return None

    # We look at the primary (first) route provided by Google
    route = directions[0]
    leg = route['legs'][0]
    
    # Calculate Congestion Index
    normal_sec = leg['duration']['value']
    traffic_sec = leg.get('duration_in_traffic', {}).get('value', normal_sec)
    
    # Ratio: 1.0 means clear, 1.5 means 50% slower than usual
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

# ==========================================
# 3. CONVERSATIONAL INTERFACE
# ==========================================

def handle_assistant_command(origin, destination, is_traffic_query=False):
    """
    The main interface for your Chatbot.
    """
    raw_data = get_maps_data(origin, destination)
    analysis = process_traffic_logic(raw_data)

    if not analysis:
        return "I'm sorry, I couldn't find any route information for that location."

    # FEATURE 1: "Drive me to..." (Direct Navigation)
    if not is_traffic_query:
        return (f"Navigating to {analysis['destination']} via {analysis['summary']}. "
                f"It is {analysis['distance']} away and will take {analysis['duration']}.")

    # FEATURE 2: "How is the traffic..." (Traffic Status)
    if is_traffic_query:
        # If there's an alternative route, we mention it
        alt_text = ""
        if len(raw_data) > 1:
            alt_route = raw_data[1]['summary']
            alt_text = f" You might consider taking {alt_route} instead."

        if analysis['congestion'] == "Clear":
            return f"Traffic is clear on {analysis['summary']}. You should reach in {analysis['duration']}."
        else:
            return (f"There is {analysis['congestion']} traffic on {analysis['summary']}. "
                    f"Expect a {analysis['delay_mins']} minute delay.{alt_text}")

# ==========================================
# 4. EXECUTION EXAMPLES
# ==========================================
if __name__ == "__main__":
    # Example 1: Navigation
    print("--- User: 'Drive me to Jaydev Vihar' ---")
    print("Assistant:", handle_assistant_command("KIIT Campus 4", "Jaydev Vihar", is_traffic_query=False))

    # Example 2: Traffic Status
    print("\n--- User: 'How is the traffic in KIIT road?' ---")
    # We query from the road's start to its end to check congestion
    print("Assistant:", handle_assistant_command("KIIT Campus 4", "Jaydev Vihar road", is_traffic_query=True))