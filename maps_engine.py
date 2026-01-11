import googlemaps
from datetime import datetime
from pathlib import Path

# ==========================================
# CONFIGURATION - Cross-platform paths
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
API_KEYS_DIR = BASE_DIR / "API_Keys"
API_KEYS_DIR.mkdir(exist_ok=True)

# Try multiple key files (for flexibility)
POSSIBLE_KEY_FILES = [
    API_KEYS_DIR / "maps_api_key.txt",
    API_KEYS_DIR / "Gemini_api_key.txt",  # Fallback to existing
]

API_KEY = None
for key_file in POSSIBLE_KEY_FILES:
    if key_file.exists():
        with open(key_file, "r", encoding="utf-8") as f:
            API_KEY = f.read().strip()
        print(f"✅ Maps API key loaded from: {key_file.name}")
        break

if not API_KEY:
    print(f"⚠️ No Maps API key found. Creating placeholder...")
    with open(API_KEYS_DIR / "maps_api_key.txt", "w") as f:
        f.write("YOUR_GOOGLE_MAPS_API_KEY_HERE")
    raise ValueError(
        f"Please add your Google Maps API key to: {API_KEYS_DIR / 'maps_api_key.txt'}\n"
        "Get one at: https://console.cloud.google.com/google/maps-apis"
    )

# Initialize Google Maps client
try:
    gmaps = googlemaps.Client(key=API_KEY)
    print("✅ Google Maps client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Maps client: {e}")
    raise

# ==========================================
# CORE FUNCTIONS
# ==========================================

def get_route_details(origin, destination):
    """
    Fetches real-time traffic and route data between two places.
    
    Args:
        origin: Starting location (address or "lat,lng")
        destination: End location (address or "lat,lng")
    
    Returns:
        Dictionary with route information or None if failed
    """
    try:
        print(f"🗺️  Calculating route: '{origin}' → '{destination}'...")
        
        # Request directions with alternatives
        directions = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=datetime.now(),  # Get real-time traffic
            alternatives=True  # Get alternative routes
        )
        
        if not directions:
            print("❌ No routes found")
            return None
        
        # Extract the first (best) route
        route = directions[0]
        leg = route['legs'][0]
        
        # Basic route data
        summary = route['summary']  # e.g., "NH16" or "Nandan Kanan Rd"
        distance = leg['distance']['text']
        duration = leg['duration']['text']
        
        # Real-time traffic data
        if 'duration_in_traffic' in leg:
            duration_traffic = leg['duration_in_traffic']['text']
            traffic_seconds = leg['duration_in_traffic']['value']
            normal_seconds = leg['duration']['value']
            delay_minutes = int((traffic_seconds - normal_seconds) / 60)
        else:
            duration_traffic = duration
            delay_minutes = 0
        
        # Alternative routes
        alternatives = []
        if len(directions) > 1:
            for alt_route in directions[1:3]:  # Up to 2 alternatives
                alternatives.append({
                    'name': alt_route['summary'],
                    'duration': alt_route['legs'][0].get('duration_in_traffic', {}).get('text', 
                                alt_route['legs'][0]['duration']['text'])
                })
        
        return {
            "summary": summary,
            "distance": distance,
            "normal_duration": duration,
            "traffic_duration": duration_traffic,
            "delay_minutes": delay_minutes,
            "start_address": leg['start_address'],
            "end_address": leg['end_address'],
            "alternatives": alternatives
        }
        
    except googlemaps.exceptions.ApiError as e:
        print(f"❌ Google Maps API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Maps Error: {e}")
        return None

# ==========================================
# RESPONSE GENERATION
# ==========================================

def generate_traffic_report(route_data):
    """
    Generates a natural language traffic report.
    
    Args:
        route_data: Dictionary from get_route_details()
    
    Returns:
        String with traffic status and advice
    """
    if not route_data:
        return "I couldn't find a route to that location. Please check the name."
    
    dest = route_data['end_address'].split(",")[0]
    traffic_time = route_data['traffic_duration']
    delay = route_data['delay_minutes']
    route_name = route_data['summary']
    
    # Determine traffic condition
    if delay < 5:
        traffic_condition = "Traffic is clear"
        advice = "It's a smooth drive."
    elif 5 <= delay < 15:
        traffic_condition = "There is moderate traffic"
        advice = f"Expect about a {delay} minute delay."
    else:
        traffic_condition = "Traffic is heavy"
        advice = f"There's a significant delay of {delay} minutes."
    
    # Build response
    response = (
        f"{traffic_condition} on the way to {dest} via {route_name}. "
        f"The trip will take about {traffic_time}. {advice}"
    )
    
    # Add alternative route suggestion if available and traffic is bad
    if delay > 10 and route_data['alternatives']:
        alt = route_data['alternatives'][0]
        response += f" You might want to consider {alt['name']}, which takes {alt['duration']}."
    
    return response

def generate_navigation_response(route_data):
    """
    Generates a navigation response (not just traffic).
    
    Args:
        route_data: Dictionary from get_route_details()
    
    Returns:
        String with navigation instructions
    """
    if not route_data:
        return "I couldn't find a route to that location. Please check the name."
    
    dest = route_data['end_address'].split(",")[0]
    distance = route_data['distance']
    duration = route_data['traffic_duration']
    route_name = route_data['summary']
    
    return (
        f"Navigating to {dest} via {route_name}. "
        f"The distance is {distance} and it will take about {duration} with current traffic."
    )

# ==========================================
# ASSISTANT COMMAND HANDLER (For chatbot_brain.py)
# ==========================================

def handle_assistant_command(origin=None, destination=None, is_traffic_query=False):
    """
    Main interface for the assistant (called by chatbot_brain.py)
    
    Args:
        origin: Starting location (if None, uses default)
        destination: End location
        is_traffic_query: True for traffic status, False for navigation
    
    Returns:
        String response for the assistant to speak
    """
    if not destination:
        return "I need a destination to provide directions."
    
    # Use default origin if not provided
    if not origin:
        origin = "KIIT Campus 4, Bhubaneswar"
        print(f"DEBUG: Using default origin: {origin}")
    
    # Get route data
    route_data = get_route_details(origin, destination)
    
    # Generate appropriate response
    if is_traffic_query:
        return generate_traffic_report(route_data)
    else:
        return generate_navigation_response(route_data)

# ==========================================
# TEST
# ==========================================
if __name__ == "__main__":
    print("="*60)
    print("MAPS ENGINE TEST")
    print("="*60)
    
    # Test 1: Traffic Report
    print("\n📍 Test 1: Traffic Query")
    response = handle_assistant_command(
        origin="Master Canteen, Bhubaneswar",
        destination="KIIT University, Patia",
        is_traffic_query=True
    )
    print(f"Response: {response}")
    
    # Test 2: Navigation
    print("\n📍 Test 2: Navigation Query")
    response = handle_assistant_command(
        origin="Master Canteen, Bhubaneswar",
        destination="Nandankanan",
        is_traffic_query=False
    )
    print(f"Response: {response}")
    
    # Test 3: No origin (uses default)
    print("\n📍 Test 3: Default Origin")
    response = handle_assistant_command(
        destination="Patia",
        is_traffic_query=False
    )
    print(f"Response: {response}")
    
    print("\n" + "="*60)