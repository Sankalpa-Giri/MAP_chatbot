import googlemaps
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
# We use the same key, but ensure "Directions API" and "Geocoding API" 
# are ENABLED in your Google Cloud Console for this key.
api = open(r"API Keys\Gemini_api_key.txt","r")
API_KEY = api.read()

# Initialize the client
gmaps = googlemaps.Client(key=API_KEY)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_route_details(origin, destination):
    """
    Fetches real-time traffic and route data between two places.
    """
    try:
        print(f"🗺️ Maps: Calculating route from '{origin}' to '{destination}'...")
        
        # Request directions
        # mode="driving": Standard car navigation
        # departure_time="now": CRITICAL! This forces Google to consider current traffic.
        directions = gmaps.directions(origin,destination,mode="driving",departure_time=datetime.now())

        if not directions:
            return None

        # Extract the first (best) route
        route = directions[0]
        leg = route['legs'][0]

        # Basic Data
        summary = route['summary']  # e.g., "NH16" or "Nandan Kanan Rd"
        distance = leg['distance']['text']
        duration = leg['duration']['text']  # Normal time (without traffic)
        
        # Real-time Traffic Data
        # 'duration_in_traffic' is only returned if departure_time is set
        if 'duration_in_traffic' in leg:
            duration_traffic = leg['duration_in_traffic']['text']
            traffic_seconds = leg['duration_in_traffic']['value']
            normal_seconds = leg['duration']['value']
            
            # Calculate Delay
            delay_seconds = traffic_seconds - normal_seconds
            delay_minutes = int(delay_seconds / 60)
        else:
            duration_traffic = duration
            delay_minutes = 0

        return {
            "summary": summary,
            "distance": distance,
            "normal_duration": duration,
            "traffic_duration": duration_traffic,
            "delay_minutes": delay_minutes,
            "start_address": leg['start_address'],
            "end_address": leg['end_address']
        }

    except Exception as e:
        print(f"Maps Error: {e}")
        return None

# ==========================================
# 3. ANALYSIS LOGIC
# ==========================================

def generate_traffic_report(route_data):
    """
    Converts raw data into a human-friendly string.
    """
    if not route_data:
        return "I couldn't find a route to that location. Please check the name."

    dest = route_data['end_address'].split(",")[0] # Shorten address
    traffic_time = route_data['traffic_duration']
    delay = route_data['delay_minutes']
    route_name = route_data['summary']

    # Logic to sound smart based on delay
    if delay < 5:
        traffic_condition = "Traffic is clear"
        advice = "It's a smooth drive."
    elif 5 <= delay < 15:
        traffic_condition = "There is moderate traffic"
        advice = f"Expect a {delay} minute delay."
    else:
        traffic_condition = "Traffic is heavy"
        advice = f"There is a significant delay of {delay} minutes. You might want to leave later."

    return (f"{traffic_condition} on the way to {dest} via {route_name}. "
            f"The trip will take about {traffic_time}. {advice}")

# --- TEST ---
if __name__ == "__main__":
    # Test with a known route (e.g., Bhubaneswar to Cuttack)
    data = get_route_details("Master Canteen, Bhubaneswar", "KIIT University, Patia")
    print(generate_traffic_report(data))