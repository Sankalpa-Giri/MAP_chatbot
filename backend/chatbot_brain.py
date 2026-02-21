# chatbot_brain.py - Response Logic

from backend import maps_engine
from backend import driver_rag
from backend.config import DEFAULT_ORIGIN

# Context storage
context = {
    "last_destination": None,
    "current_location": None,   # can be updated dynamically
    "history": []
}

# ==========================================
# MAIN RESPONSE FUNCTION
# ==========================================

def get_bot_response(nlu_result: dict, original_text: str, current_location=None) -> str:
    global context

    intent = nlu_result.get("intent", "unknown")

    # Update current location if provided
    if current_location:
        context["current_location"] = current_location

    # Use dynamic location if available, else fall back to default
    origin = context["current_location"] or DEFAULT_ORIGIN

    # STOP COMMAND
    if intent == "stop":
        return "stop_now"

    # TRAFFIC/ROUTE REQUEST
    if intent == "get_route_traffic":
        destination      = nlu_result.get("destination")
        wants_directions = nlu_result.get("wants_directions", False)

        print(f"📍 Destination: {destination}, Directions: {wants_directions}, Origin: {origin}")

        # Handle follow-up references
        if not destination or destination.lower() in ["there", "it", "that"]:
            destination = context["last_destination"]
            if not destination:
                return "Where would you like to go?"

        # ── Clean destination name ─────────────────────────────────────────
        # Remove command words that leaked into the destination
        # e.g. "Directions Nayapalli" → "Nayapalli"
        import re
        command_prefixes = [
            "directions to", "directions", "navigate to", "navigate",
            "take me to", "go to", "route to", "traffic to",
            "how to get to", "how to go to", "show me", "guide me to"
        ]
        dest_clean = destination.lower().strip()
        for prefix in command_prefixes:
            if dest_clean.startswith(prefix):
                destination = destination[len(prefix):].strip()
                break
        destination = destination.strip().title()

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
                return f"I don't have your {destination} saved. Say 'remember my {destination} is at [address]'."

        # Validate destination
        if not destination or len(destination.strip()) < 2:
            return "I didn't catch where you want to go. Can you repeat?"

        # Get route (picks fastest of up to 3 alternatives automatically)
        route = maps_engine.get_route_data(origin, destination, get_steps=wants_directions)

        # Handle errors
        if "error" in route:
            if route.get("message"):
                return route["message"]
            return f"I couldn't find a route to {destination}. Try saying it differently."

        # Save for follow-ups
        context["last_destination"] = destination

        # ── Build response ─────────────────────────────────────────────────
        if wants_directions and "steps" in route and len(route["steps"]) > 0:
            steps = route["steps"]

            # Show max 4 key turn steps — concise for voice/chat
            key_steps = steps[:4]

            reply = f"To {route['destination']}: "
            reply += ". Then ".join(key_steps)
            reply += f". {route['distance']}, {route['duration']}. {route['traffic_desc']}."

        else:
            # Traffic summary mode
            reply = f"{route['destination']} is {route['distance']} away. "
            reply += f"{route['duration']} via {route['route_name']}. "
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
            return "I'm best at helping with traffic and directions. Try asking me about a destination!"

def update_location(new_location: str):
    """Call this to update the driver's current location dynamically"""
    global context
    context["current_location"] = new_location
    print(f"📍 Location updated: {new_location}")

def clear_context():
    global context
    context = {"last_destination": None, "current_location": None, "history": []}