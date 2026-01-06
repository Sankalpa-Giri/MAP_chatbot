import google.generativeai as genai
import maps_engine
import weather_engine
import spotify_music
import connect_phone

# ==========================================
# CONFIGURATION
# ==========================================
api = open(r"API Keys\Gemini_api_key.txt", "r")
API_KEY = api.read()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# LLM FOR CONVERSATION
# ==========================================
def query_llm(user_text):
    """Get conversational response from Gemini"""
    try:
        prompt = f"You are a helpful voice assistant. Keep your answer short and conversational (under 2 sentences). User said: {user_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"I'm having trouble connecting right now."

# ==========================================
# MAIN RESPONSE ROUTER
# ==========================================
def get_bot_response(nlu_result, original_text):
    """
    Main response handler for all intents
    
    Args:
        nlu_result: Dict from nlu_engine_control()
        original_text: Original user speech
    
    Returns:
        String response to speak
    """
    intent = nlu_result['intent']
    
    # --- WEATHER ---
    if intent == 'get_weather':
        location = nlu_result.get('location', 'Bhubaneswar')
        print(f"DEBUG: Weather request for {location}")
        return weather_engine.get_weather_report(location)
    
    # --- TRAFFIC ---
    elif intent == 'get_route_traffic':
        dest = nlu_result.get('destination')
        origin = nlu_result.get('origin')
        
        if not dest:
            return "I can check the traffic, but I need to know where you want to go."
        
        # Use provided origin or default
        if not origin:
            origin = "KIIT Campus 4, Bhubaneswar"
            print(f"DEBUG: No origin specified, using default: {origin}")
        else:
            print(f"DEBUG: Using specified origin: {origin}")
        
        print(f"DEBUG: Routing from '{origin}' to '{dest}'")
        
        # Get route data
        route_data = maps_engine.get_route_details(origin, dest)
        
        if not route_data:
            return f"I couldn't find a route to {dest}. Please check the location name."
        
        # Generate traffic report
        traffic_report = maps_engine.generate_traffic_report(route_data)
        
        # Try to send to phone
        try:
            success = connect_phone.send_navigation_link(dest)
            if success:
                return f"{traffic_report} I have also sent the directions to your phone."
        except:
            pass
        
        return traffic_report
    
    # --- MUSIC ---
    elif intent == 'get_music':
        song = nlu_result.get('song')
        if song:
            return spotify_music.play_music(song)
        else:
            return "I couldn't identify which song you want to play. Could you repeat that?"
    
    # --- PHONE ---
    elif intent == "find_phone":
        return connect_phone.find_my_phone()
    
    # --- CONVERSATION ---
    else:
        return query_llm(original_text)

# ==========================================
# TEST ZONE
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("CHATBOT BRAIN TEST")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {"intent": "get_weather", "location": "Cuttack"},
        {"intent": "get_route_traffic", "origin": "Master Canteen", "destination": "KIIT"},
        {"intent": "get_route_traffic", "origin": None, "destination": "Patia"},
        {"intent": "get_music", "song": "tum hi ho"},
        {"intent": "unknown", "text": "hello"}
    ]
    
    for i, test_nlu in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_nlu}")
        print("-" * 60)
