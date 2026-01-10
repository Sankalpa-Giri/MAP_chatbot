import maps_engine
import weather_engine
import spotify_music
import connect_phone
import driver_rag
# ==========================================
# CONFIGURATION
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
            
            is_traffic_query = "traffic" in original_text.lower()
            # 2. Call Real Maps API
            route_data = maps_engine.handle_assistant_command(origin, dest,is_traffic_query)

            return route_data
        else:
            return "I can check the traffic, but I need to know the destination."

    # --- PATH C: MUSIC ---
    elif intent == 'get_music':
        music_query = nlu_result.get('song')
        if music_query:
            return spotify_music.play_music(music_query)  
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
