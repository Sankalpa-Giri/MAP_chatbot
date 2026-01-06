import maps_engine
import weather_engine
import spotify_music
import connect_phone
import driver_rag
# ==========================================
# 1. CONFIGURATION
# ==========================================
'''There is no configuration, all the files related to llm has been moved to driver_rag.py'''
# ==========================================
# 2. THE GENERAL BRAIN (phi3:mini)
# ==========================================
def query_llm(user_text):
    """
    Sends the user's text to Ollama Flash for a conversational reply.
    """
    try:
        # 1. Try to store memory
        memory_resp = driver_rag.store_memory(user_text)
        if memory_resp:
            print("Assistant:", memory_resp)

        # 2. Try to forget memory
        forget_resp = driver_rag.delete_memory(user_text)
        if forget_resp:
            print(f"Assistant: {forget_resp}")

        return driver_rag.ask_llm(user_text)
    
    except Exception as e:
        return f"I'm having trouble connecting to my LLM. (Error: {e})"

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
            #-----RAG check step-----
            if dest.lower() in ["home","office","word","gym"]:
                rag_address = driver_rag.query_chroma(f"What is my {dest} address?")
                if "I don't know that yet." not in rag_address:
                    dest = rag_address
            #------------------------
            # 1. Decide Origin (For now, hardcode or use a default)
            # In a real app, you'd use GPS or ask the user "Where are you starting?"
            origin = "kiit campus 4" 
            
            # 2. Call Real Maps API
            route_data = maps_engine.get_route_details(origin, dest)
            
            # 3. Generate Report
            traffic_report = maps_engine.generate_traffic_report(route_data)

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
    
