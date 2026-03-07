"""
Action performer module.
Handles execution of specific actions based on intents and domains.
"""
from ActionHandlers import navigation_handler, weather_handler, traffic_status_handler, memory_handler
from Generate.generate_response import chat


def perform_action(routeInfo: dict, domain: str, original_text: str, session_id: str) -> dict:
    """
    Central dispatcher: routes to the correct action handler based on domain.

    Parameters:
        routeInfo     : NLU output (intent, entities, is_dependent, user_location)
        domain        : Domain string emitted by identify_domain.parse_domain()
        original_text : Raw user message (passed to handlers that need it)
        session_id    : Active session identifier

    Returns:
        dict with at minimum a "reply" key
    """

    if domain == "DOMAIN_NAVIGATION":
        reply = navigation_handler.navigation_action(routeInfo=routeInfo, session_id=session_id)

    elif domain == "DOMAIN_WEATHER":
        reply = weather_handler.weather_action(routeInfo=routeInfo, text=original_text, session_id=session_id)

    elif domain == "DOMAIN_TRAFFIC_STATUS":
        reply = traffic_status_handler.traffic_status_action(routeInfo=routeInfo, text=original_text, session_id=session_id)

    elif domain == "DOMAIN_MEMORY":
        reply = memory_handler.memory_action(routeInfo=routeInfo, text=original_text, session_id=session_id)

    elif domain == "DOMAIN_CHITCHAT":
        reply = chat(text=original_text)

    else:
        return {
            "reply": f"Unrecognised domain: '{domain}'. Cannot process request.",
            "action": "ERROR",
            "data": {"domain": domain}
        }

    return reply