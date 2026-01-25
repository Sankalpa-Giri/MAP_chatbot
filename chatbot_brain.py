import maps_engine
import weather_engine
import spotify_music
import driver_rag


# ==========================================
# 2. THE GENERAL BRAIN (phi3:mini)
# ==========================================
def query_llm(user_text: str) -> dict:
    """
    Query the local LLM using RAG.
    Returns structured response.
    """
    try:
         # Memory operations (silent)
        driver_rag.store_memory(user_text)
        driver_rag.delete_memory(user_text)

        llm_reply = driver_rag.ask_llm(user_text)

        return llm_reply["reply"]
    
    except Exception as e:
        return "I'm having trouble connecting to my language model."
    
# ==========================================
# 3. THE ROUTER (The Decision Maker)
# ==========================================
def get_bot_response(nlu_result: dict, original_text: str, current_location=None) -> dict:
    intent = nlu_result.get("intent", "UNKNOWN")
    
    # -------- WEATHER --------
    if intent == "GET_WEATHER":
        location = nlu_result.get("entities", {}).get("location")

        if location is None:
            return {
                'code': "LOCATION_MISSING",
                'details': "I need a location to check the weather",
                'action': 'ERROR',
                'data': original_text
            }

        weather_data = weather_engine.get_weather_report(location)

        reply = (
                f"The current temperature in {weather_data['city']} is "
                f"{weather_data['temperature_c']} degrees Celsius. "
                f"It feels like {weather_data['feels_like_c']} degrees. "
                f"Conditions are {weather_data['description']}."
                )

        return reply

    # -------- TRAFFIC / ROUTE --------
    elif intent == "GET_ROUTE_TRAFFIC":
        destination = nlu_result.get("entities", {}).get("destination")

        if not destination:
            return {
                "code": "MISSING_DESTINATION",
                "reply": "I need a destination to check the route.",
                "action": "CLARIFY",
                "data": {}
            }

        # RAG location resolution
        if destination.lower() in ["home", "office", "college", "gym"]:
            rag_address = driver_rag.retrieve_memory(
                f"What is my {destination} address?"
            )
            if "I don't know" not in rag_address:
                destination = rag_address

        origin = current_location or "KIIT Campus 4"
        is_traffic_query = True if "traffic" in original_text.lower() else False

        route_data = maps_engine.get_route_data(
            origin=origin,
            destination=destination,    
            traffic=is_traffic_query
        )

        return {
            "reply": f"Here is the route to {destination}.",
            "action": "NAVIGATION",
            "data": route_data
        }

    # -------- MUSIC --------
    elif intent == "GET_MUSIC":
        song = nlu_result.get("entities", {}).get("song")

        track_data = spotify_music.search_track(song)

        if "error" in track_data:
            return {
                "code": "TRACK_NOT_FOUND",
                "details": f"I couldn't find {song}.",
                "action": "ERROR",
                "data": track_data
                }

        return {
            "reply": f"Playing {track_data['track_name']} by {track_data['artist']}.",
            "action": "SPOTIFY_PLAY",
            "data": track_data
            }

    # -------- FALLBACK TO LLM --------
    else:
        return query_llm(original_text)
    
