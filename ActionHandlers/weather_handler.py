import FetchServices.fetch_weather as fetch_weather
import Generate.generate_response_weather as generate_response_weather
import conversation_store

# ==========================================
# ACTION
# ==========================================

def weather_action(routeInfo: dict, text: str, session_id: str):

    location = None
    weather_data = None
    
    entities = routeInfo.get("entities", {})
    user_location = routeInfo.get("user_location", {})
    is_dependent = routeInfo.get("is_dependent", False)
    state = conversation_store.get_session(session_id)
    
    try:
        # 2. Resolve the target location
        # Priority 1: Explicitly mentioned in text
        # Priority 2: Resolved from history (dependent)
        # Priority 3: Fallback to coordinates (if location remains None)
        
        location = entities.get("destination")
        
        # If NLU didn't resolve it but flagged it as dependent, check state
        if not location and is_dependent:
            location = state.last_location

        # 3. Fetch Weather Data
        if location:
            weather_data = fetch_weather.get_weather_report(location)
            
        # 4. Coordinate Fallback (Implicit Location)
        # We trigger this if no location was found OR if the named search failed
        if not weather_data:
            lat = user_location.get("latitude")
            lon = user_location.get("longitude")
            
            if lat and lon:
                weather_data = fetch_weather.get_weather_by_coordinates(lat=lat, lon=lon)

        # 5. Response Handling
        if weather_data:
            reply = generate_response_weather.summarize(weather=weather_data, user_query=text)
            return {"reply": reply, "action": "REPLY", "data": weather_data}

        # 6. Clarification Required
        return {
            "reply": "Which city's weather would you like to know?",
            "action": "CLARIFY",
            "data": {"missing": "location"}
        }

    except Exception as e:
        # location is now safely initialized as None or a String
        error_loc = location or "your current location"
        return {
            "reply": f"I couldn't fetch the weather for {error_loc} right now.",
            "action": "ERROR", 
            "data": {"error": str(e)}
        }