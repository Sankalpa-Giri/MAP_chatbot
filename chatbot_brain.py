import maps_engine
import driver_rag

context = {
    "last_destination": None,
    "history": []
}

def get_bot_response(nlu_result: dict, original_text: str, current_location=None) -> str:
    """
    TRAFFIC-FIRST BOT with robust error handling
    """
    global context
    
    intent = nlu_result.get("intent", "unknown")
    
    # Stop command
    if intent == "stop":
        return "stop_now"
    
    # TRAFFIC/ROUTE REQUEST
    if intent == "get_route_traffic":
        destination = nlu_result.get("destination")
        wants_directions = nlu_result.get("wants_directions", False)
        
        print(f"📍 Destination: {destination}, Directions: {wants_directions}")
        
        # Handle follow-up references
        if not destination or destination.lower() in ["there", "it", "that"]:
            destination = context["last_destination"]
            if not destination:
                return "Where would you like to go?"
        
        # Resolve saved locations
        if destination and destination.lower() in ["home", "office", "gym", "work"]:
            saved = driver_rag.retrieve_context(f"{destination}")
            
            if saved and "no memory" not in saved.lower():
                found_address = None
                
                for line in saved.split('\n'):
                    line = line.strip('- ').strip()
                    
                    if "is at" in line.lower():
                        parts = line.lower().split("is at")
                        if len(parts) > 1:
                            found_address = parts[-1].strip()
                    elif ":" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            found_address = parts[-1].strip()
                    else:
                        if destination.lower() not in line.lower() or len(line.split()) > 2:
                            found_address = line
                
                if found_address:
                    found_address = found_address.replace("my", "").strip()
                    found_address = found_address.replace(destination.lower(), "").strip()
                    
                    if len(found_address) > 2:
                        destination = found_address.title()
                        print(f"✅ Using saved: {destination}")
                    else:
                        return f"The address for {destination} seems incomplete."
                else:
                    return f"I couldn't find the address for {destination}."
            else:
                return f"I don't have your {destination} saved. Say 'remember my {destination} is at' followed by the address."
        
        # Validate destination exists
        if not destination or len(destination.strip()) < 2:
            return "I didn't catch where you want to go. Can you repeat the destination?"
        
        # Get route with traffic
        route = maps_engine.get_route_data("KIIT Campus 4", destination, get_steps=wants_directions)
        
        # Handle errors
        if "error" in route:
            if route.get("message"):
                return route["message"]
            return f"I couldn't find a route to {destination}. Can you try saying it differently?"
        
        # Save for follow-ups
        context["last_destination"] = destination
        
        # BUILD RESPONSE
        if wants_directions and "steps" in route and len(route["steps"]) > 0:
            # Directions mode
            reply = f"To get to {route['destination']}: {route['steps'][0]}. "
            if len(route["steps"]) > 1:
                reply += f"Then {route['steps'][1]}. "
            reply += f"Total distance is {route['distance']}, takes {route['duration']}. "
            reply += f"{route['traffic_desc']}."
        else:
            # Traffic summary mode (DEFAULT)
            reply = f"{route['destination']} is {route['distance']} away. "
            reply += f"It will take {route['duration']} via {route['route_name']}. "
            reply += f"{route['traffic_desc']}."
        
        context["history"].append(f"Route to {destination}")
        return reply
    
    # MEMORY OPERATIONS
    else:
        memory_resp = driver_rag.handle_memory_ops(original_text)
        if memory_resp:
            context["history"].append(f"Memory: {original_text}")
            return memory_resp
        
        # GENERAL CONVERSATION
        try:
            reply = driver_rag.ask_llm(original_text, context["history"])
            context["history"].append(reply)
            if len(context["history"]) > 5:
                context["history"].pop(0)
            return reply
        except Exception as e:
            print(f"⚠️ LLM error: {e}")
            return "I'm not sure about that. I'm best at helping with traffic and directions in Bhubaneswar."

def clear_context():
    """Reset conversation context"""
    global context
    context = {"last_destination": None, "history": []}