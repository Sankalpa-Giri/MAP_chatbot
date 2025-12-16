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
# 🔑 Get your FREE key here: https://aistudio.google.com/app/apikey
# Paste it inside the quotes below
api = open(r"API Keys\Gemini_api_key.txt","r")
API_KEY = api.read()

# Configure the Google AI library
genai.configure(api_key=API_KEY)

# Initialize the 'Flash' model (Fast & Free Tier) 
# We use 'gemini-2.0-flash' specifically for speed and cost.
model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 2. THE GENERAL BRAIN (Gemini 2.0 Flash)
# ==========================================
def query_llm(user_text):
    """
    Sends the user's text to Gemini Flash for a conversational reply.
    """
    try:
        # We ask Gemini to be concise since it's a voice assistant
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
            # If no city heard, assume current city or ask Gemini
            return weather_engine.get_weather_report("Bhubaneswar")

    # --- PATH B: TRAFFIC ---
    elif intent == 'get_route_traffic':
        dest = nlu_result['destination']
        if dest:
            # 1. Decide Origin (For now, hardcode or use a default)
            # In a real app, you'd use GPS or ask the user "Where are you starting?"
            origin = "kiit campus 4" 
            
            # 2. Call Real Maps API
            route_data = maps_engine.get_route_details(origin, dest)
            
            # 3. Generate Report
            traffic_report = maps_engine.generate_traffic_report(route_data)
        
            success = connect_phone.send_navigation_link(dest)
            if success:
                return f"{traffic_report}. I have also sent the directions to your phone for the drive."
            else:
                return traffic_report
        else:
            return "I can check the traffic, but I need to know the destination."

    # --- PATH C: MUSIC ---
    elif intent == 'get_music':
        music_query = nlu_result.get('song')
        if music_query:
            return spotify_music.play_music(music_query)
        else:
            return "I could not find the song or the artist"

    # --- PATH D: FIND PHONE ---
    elif intent == "find_phone":
        return connect_phone.find_my_phone()
    
    # --- PATH E: OPEN MAPS APP ---


    else:
        # Gemini Logic
        return query_llm(original_text)
    
