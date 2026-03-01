from typing import Optional, cast
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import logging
import conversation_store

logger = logging.getLogger(__name__)

class Entities(BaseModel):
    location: Optional[str] = None
    destination: Optional[str] = None
    song: Optional[str] = None
    contact: Optional[str] = None

class NLUResult(BaseModel):
    intent: str = Field(description="One of: GET_WEATHER, GET_ROUTE, GET_TRAFFIC, GET_ALTERNATE_ROUTE, GET_MUSIC, GET_PHONE, UNKNOWN")
    entities: Entities = Field(default_factory=lambda: Entities())
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    assumptions: list[str] = Field(default_factory=list,description="Assumptions made e.g. missing_destination, default_location")
    is_followup: bool = Field(False,description="True if user refers to a previous place (there, that place, same spot)")

_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an intent parser for an in-car voice assistant in Bhubaneswar, India.
Analyze the user's message and extract intent and entities.

INTENTS:
- GET_ROUTE          : user wants step-by-step directions or navigation to a place
- GET_TRAFFIC        : user wants ONLY traffic conditions, delay, or congestion info
- GET_ALTERNATE_ROUTE: user wants alternative/other routes to a place
- GET_WEATHER        : user asks about weather, rain, temperature, forecast
- GET_MUSIC          : user wants to play a song, artist, playlist, or resume music
- GET_PHONE          : user wants to call, text, or message someone
- UNKNOWN            : anything else

INTENT DISAMBIGUATION — TRAFFIC vs ROUTE vs ALTERNATE:
- "take me to X", "navigate to X", "directions to X", "how do I get to X" → GET_ROUTE
- "traffic to X", "how's traffic to X", "is there congestion on the way to X" → GET_TRAFFIC
- "alternate route", "other route", "different way", "avoid traffic route" → GET_ALTERNATE_ROUTE     

ENTITY RULES:
- location    : extract for GET_WEATHER (e.g. "weather in Cuttack" → Cuttack)
- destination : extract for GET_ROUTE_TRAFFIC (e.g. "take me to AIIMS" → AIIMS)
- song        : extract for GET_MUSIC (e.g. "play Believer" → Believer)
- contact     : extract for GET_PHONE (e.g. "call mom" → mom)

FOLLOW-UP DETECTION:
- If user says "take me there", "go there", "same place", "that location", "it" referring
  to a place → set is_followup: true, leave destination: null
- Use conversation history to understand what "there" refers to — but do NOT resolve it 
  yourself, just flag it

ASSUMPTIONS:
- If intent is clear but entity is missing, add to assumptions:
  missing_destination, missing_location, missing_song, missing_contact
- If assuming user's current city for weather, add: default_location

CONFIDENCE:
- 0.9+ : clear explicit request
- 0.7  : probable but slightly ambiguous
- 0.5  : inferred from weak signals
- 0.3  : very uncertain → set intent to UNKNOWN

EXAMPLES:
"take me to AIIMS"                → GET_ROUTE, destination: AIIMS, confidence: 0.95
"how's traffic to AIIMS"          → GET_TRAFFIC, destination: AIIMS, confidence: 0.95
"any alternate route to AIIMS"    → GET_ALTERNATE_ROUTE, destination: AIIMS, confidence: 0.95
"take me there"                   → GET_ROUTE, is_followup: true, destination: null
"traffic there"                   → GET_TRAFFIC, is_followup: true, destination: null
"what's the weather like"         → GET_WEATHER, no location, assumptions: [default_location]
"weather in Cuttack"              → GET_WEATHER, location: Cuttack, confidence: 0.95
"play something chill"            → GET_MUSIC, song: null, assumptions: [missing_song]
"play Arijit Singh"               → GET_MUSIC, song: Arijit Singh, confidence: 0.9
"call Rahul"                      → GET_PHONE, contact: Rahul, confidence: 0.95
"what causes traffic jams"        → UNKNOWN, confidence: 0.3
"""),
    ("human", "Conversation so far:\n{history}\n\nLatest message: {user_input}")
])

_llm = ChatOllama(model="llama3.1:8b", temperature=0, num_predict=150, keep_alive=-1)
_nlu_chain = _prompt | _llm.with_structured_output(NLUResult)

def parse_intent(text: str,  session_id: str = "default") -> dict:
    """
    Parses intent with conversation history context.
    Resolves follow-up references (there, same place) from session memory.
    """
    if not text or not text.strip():
        return {
            "intent": "UNKNOWN",
            "entities": {},
            "confidence": 0.0,
            "assumptions": [],
            "is_followup": False
        }

    try:
        session = conversation_store.get_session(session_id)
        history = session.get_history_text()

        result = cast(NLUResult, _nlu_chain.invoke({
            "history": history or "No prior conversation.",
            "user_input": text
        }))

        entities = result.entities.model_dump(exclude_none=True)

        # Resolve follow-up references from session
        if result.is_followup and result.intent in ("GET_ROUTE", "GET_TRAFFIC", "GET_ALTERNATE_ROUTE"):
            if not entities.get("destination"):
                if session.last_destination:
                    entities["destination"] = session.last_destination
                    entities["resolved_from_history"] = True
                    logger.info(f"Resolved follow-up → '{session.last_destination}'")
                else:
                    result.assumptions.append("missing_destination")    

            elif result.intent == "GET_WEATHER" and not entities.get("location"):
                if session.last_location:
                    entities["location"] = session.last_location
                    entities["resolved_from_history"] = True
                else:
                    result.assumptions.append("missing_location")

        logger.info(f"NLU → intent={result.intent} confidence={result.confidence} followup={result.is_followup}")

        return {
            "intent": result.intent,
            "entities": entities,
            "confidence": result.confidence,
            "assumptions": result.assumptions,
            "is_followup": result.is_followup,
            "session_id": session_id
        }



    except Exception as e:
        logger.error(f"NLU chain failed: {e}")
        return {
            "intent": "UNKNOWN",
            "entities": {},
            "confidence": 0.0,
            "assumptions": ["nlu_failure"],
            "is_followup": False
        }