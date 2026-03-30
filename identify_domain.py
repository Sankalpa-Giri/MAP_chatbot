from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config import MODEL
from pydantic import BaseModel, Field
from typing import cast


class Domain(BaseModel):
    domain: str = Field(description="Identify the domain to narrow intent search")


_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a domain classifier in a NLU engine.
Your job is to pick exactly one domain from the list below for the given user message.

DOMAINS AND THEIR MEANING:

DOMAIN_WEATHER
  The user wants to know about weather conditions.
  Keywords: weather, temperature, rain, hot, cold, windy, cloudy, forecast, sunny
  Examples:
  - "how is the weather in Cuttack"
  - "will it rain today"
  - "is it hot outside"

DOMAIN_NAVIGATION
  The user wants turn-by-turn directions or a route to a place.
  Keywords: route, navigate, directions, take me to, show me the way, go to
  Examples:
  - "show me the route to Silicon University"
  - "take me to Zudio Nayapalli"
  - "navigate to AIIMS Bhubaneswar"
  - "how do I get to DAV school"

DOMAIN_TRAFFIC_STATUS
  The user wants to know about traffic conditions, travel time, ETA, or distance — NOT directions.
  Keywords: traffic, how long, how far, how much time, distance, time to reach, ETA, delay, congestion, is there traffic
  Examples:
  - "how far is DAV school unit 8"
  - "how much time will it take to reach DAV school"
  - "is there any traffic on the way to DAV school"
  - "how long to reach Cuttack"
  - "what is the ETA to the office"
  - "how is the traffic to KIIT"

DOMAIN_MEMORY
  The user wants to save, update, delete, OR LOOK UP a remembered address.
  Keywords: save, remember, memorize, forget, delete, update, what is my, where is my, tell me my
  Examples:
  - "save my office address as Infocity Square"
  - "remember my home is 42 MG Road"
  - "forget my gym address"
  - "update my office to Patia Square"
  - "what is my office address"
  - "where is my home"
  - "tell me my gym address"
     
DOMAIN_DISCOVER
  The user wants to find nearby places of a category — food, cafes, hospitals, fuel, etc.
  They have not named a specific destination. They want a suggestion or the nearest match.
  Keywords: near me, nearby, around me, somewhere nice, grab food, find a, any good, closest
  Examples:
  - "what's near me"
  - "take me somewhere nice"
  - "bro I wanna grab food nearby"
  - "find a cafe around here"
  - "any good restaurants near me"
  - "I need fuel"
  - "find me the nearest atm"

DOMAIN_CHITCHAT
  General conversation, greetings, jokes, or questions not related to navigation or weather.
  Examples:
  - "hello"
  - "tell me a joke"
  - "what are the traffic light colours"
  - "thank you"

CRITICAL RULES:
- If the user asks for a ROUTE or DIRECTIONS → DOMAIN_NAVIGATION
- If the user asks HOW LONG, HOW FAR, TRAFFIC CONDITIONS, or ETA → DOMAIN_TRAFFIC_STATUS
- Never confuse DOMAIN_NAVIGATION with DOMAIN_TRAFFIC_STATUS.
  NAVIGATION = the user wants to be guided step by step.
  TRAFFIC_STATUS = the user wants information about time, distance, or traffic.
"""),
    ("human", "User text: {text}")
])

_llm = ChatOllama(model=MODEL, temperature=0.0, num_predict=30, keep_alive=-1)
_structured_llm = _llm.with_structured_output(Domain)
_chain = _prompt | _structured_llm


def parse_domain(text: str) -> dict:
    if not text or not text.strip():
        return {
            "domain": "UNKNOWN",
            "descp": "Empty input text"
        }

    try:
        result = cast(Domain, _chain.invoke({"text": text}))
        return {
            "domain": result.domain if result else "DOMAIN_CHITCHAT"
        }

    except Exception as e:
        return {
            "domain": "UNKNOWN",
            "descp": f"Ollama offline: {str(e)}"
        }


if __name__ == "__main__":
    tests = [
        "how far is DAV school unit 8",
        "how much time will it take to reach DAV school unit 8",
        "is there any traffic on way to DAV school unit 8",
        "show me the route to Silicon University",
        "how is the weather in Cuttack",
        "save my office as Infocity Square",
        "hello",
    ]
    for t in tests:
        result = parse_domain(t)
        print(f"{t!r:60s} -> {result.get('domain')}")