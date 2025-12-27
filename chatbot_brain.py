import random
import os
import google.generativeai as genai
import maps_engine
import weather_engine
import spotify_music
import connect_phone

# ==========================================
# 1. CONFIGURATION
# ==========================================
api = open(r"API Keys\Gemini_api_key.txt","r")
API_KEY = api.read()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 2. THE GENERAL BRAIN (Gemini 2.0 Flash)
# ==========================================
def query_llm(user_text):
    """
    Sends the user's text to Gemini Flash for a conversational reply.
    """
    try:
        prompt = f"You are a helpful voice assistant. Keep your answer short and conversational (under 2 sentences). User said: {user_text}"
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"I'm having trouble connecting to my brain. (Error: {e})"

# ==========================================
# 3. THE ROUTER (The Decision Maker)
# ==========================================
def get_bot_response(nlu_result, original_text):
    intent = nlu_result['intent']
    
    # --- PATH A: WEATHER ---
    if intent == 'get_weather':
        location = nlu_result.get('location')
        if location:
            print(f"DEBUG: Checking weather for {location}")
            return weather_engine.get_weather_report(location)
        else:
            return weather_engine.get_weather_report("Bhubaneswar")
    
    # --- PATH B: TRAFFIC ---
    elif intent == 'get_route_traffic':
        dest = nlu_result.get('destination')
        origin = nlu_result.get('origin')
        
        if dest:
            # Use provided origin or default to KIIT Campus 4
            if not origin:
                origin = "KIIT Campus 4, Bhubaneswar"
                print(f"DEBUG: No origin specified, using default: {origin}")
            else:
                print(f"DEBUG: Using specified origin: {origin}")
            
            print(f"DEBUG: Routing from '{origin}' to '{dest}'")
            
            # Call Real Maps API
            route_data = maps_engine.get_route_details(origin, dest)
            
            # Generate Report
            traffic_report = maps_engine.generate_traffic_report(route_data)
        
            # Try to send to phone
            success = connect_phone.send_navigation_link(dest)
            if success:
                return f"{traffic_report} I have also sent the directions to your phone for the drive."
            else:
                return traffic_report
        else:
            return "I can check the traffic, but I need to know the destination. Where do you want to go?"
    
    # --- PATH C: MUSIC ---
    elif intent == 'get_music':
        music_query = nlu_result.get('song')
        if music_query:
            return spotify_music.play_music(music_query)
        else:
            return "I couldn't identify which song you want to play. Could you repeat that?"
    
    # --- PATH D: FIND PHONE ---
    elif intent == "find_phone":
        return connect_phone.find_my_phone()
    
    # --- PATH E: GENERAL CONVERSATION ---
    else:
        return query_llm(original_text)


# ==========================================
# 4. TEST ZONE
# ==========================================
if __name__ == "__main__":
    # Test with mock NLU results
    print("=" * 50)
    print("Testing Chatbot Brain")
    print("=" * 50)
    
    # Test 1: Weather
    test1_nlu = {"intent": "get_weather", "location": "Cuttack"}
    print(f"\nTest 1 - Weather: {test1_nlu}")
    # Uncomment if weather_engine is available:
    # print(get_bot_response(test1_nlu, "weather in Cuttack"))
    
    # Test 2: Traffic with origin and destination
    test2_nlu = {"intent": "get_route_traffic", "origin": "Master Canteen", "destination": "KIIT"}
    print(f"\nTest 2 - Traffic (with origin): {test2_nlu}")
    # Uncomment if maps_engine is available:
    # print(get_bot_response(test2_nlu, "drive from Master Canteen to KIIT"))
    
    # Test 3: Traffic with only destination
    test3_nlu = {"intent": "get_route_traffic", "origin": None, "destination": "Patia"}
    print(f"\nTest 3 - Traffic (destination only): {test3_nlu}")
    # Uncomment if maps_engine is available:
    # print(get_bot_response(test3_nlu, "take me to Patia"))
    
    print("\n" + "=" * 50)
