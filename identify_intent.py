from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import cast, Optional, Any
from config import MODEL, REFERENCE_WORDS
import conversation_store
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
)
logger = logging.getLogger(__name__)


class Intent(BaseModel):
    intent: str = Field(description="Intent of the text")
    entity: Optional[str] = Field(None, description="Entity/Place mentioned in the string")


_prompt_weather = ChatPromptTemplate.from_messages([
    ("system", """You are an intent and entity parser.
Analyze the user's message and extract the intent and the place name.

INTENTS:
- GET_WEATHER: weather, rain, temperature, forecast

EXTRACTION RULES:
- Extract the actual place name the user mentions (a city, area, or location name).
- If the user says a referential word like "there", "here", or "it", extract that exact word.
- Never output the word "destination" — output the real place name from the message.

EXAMPLES:
"weather in Cuttack"             -> intent: GET_WEATHER, entity: "Cuttack"
"how is the weather in Mumbai"   -> intent: GET_WEATHER, entity: "Mumbai"
"will it rain there"             -> intent: GET_WEATHER, entity: "there"
"is it hot in Delhi"             -> intent: GET_WEATHER, entity: "Delhi"
"""),
    ("human", """Latest message: {user_input}""")
])

_prompt_navigation = ChatPromptTemplate.from_messages([
    ("system", """You are an intent and entity parser.
Analyze the user's message and extract the intent and the place name.

INTENTS:
- GET_ROUTE           : step-by-step directions or navigation to a place
- GET_ALTERNATE_ROUTE : alternative or other routes

EXTRACTION RULES:
- Extract the actual place name the user wants to go to.
- If the user says a referential word like "there", "here", or "it", extract that exact word.
- If the user names a new place explicitly, extract it — ignore conversation history.
- Never output the word "destination" — output the real place name from the message.

EXAMPLES:
"take me to Zudio Nayapalli"         -> intent: GET_ROUTE, entity: "Zudio Nayapalli"
"show me the route to Silicon University" -> intent: GET_ROUTE, entity: "Silicon University"
"navigate to AIIMS Bhubaneswar"      -> intent: GET_ROUTE, entity: "AIIMS Bhubaneswar"
"take me there"                      -> intent: GET_ROUTE, entity: "there"
"find alternate routes"              -> intent: GET_ALTERNATE_ROUTE, entity: "there"
"""),
    ("human", """Conversation so far:\n{history}\n\nLatest message: {user_input} """)
])

_prompt_memory = ChatPromptTemplate.from_messages([
    ("system", """You are an intent and entity parser.
Analyze the user's message and extract the intent and the address or place name.

INTENTS:
- SAVE_ADDRESS   : save, memorize, or remember an address
- DELETE_ADDRESS : delete or forget an address
- UPDATE_ADDRESS : modify or update an existing address
- GET_ADDRESS    : ask what a saved address is, or where a saved label is

EXTRACTION RULES:
- Extract the label (home, office, gym) or the address the user mentions.
- Never output the word "destination" — output the real label or address.

EXAMPLES:
"save my office as Infocity Square"  -> intent: SAVE_ADDRESS,  entity: "Infocity Square"
"remember my home is 42 MG Road"     -> intent: SAVE_ADDRESS,  entity: "42 MG Road"
"forget my gym address"              -> intent: DELETE_ADDRESS, entity: "gym"
"update my office to Patia Square"   -> intent: UPDATE_ADDRESS, entity: "Patia Square"
"what is my office address"          -> intent: GET_ADDRESS,    entity: "office"
"where is my home"                   -> intent: GET_ADDRESS,    entity: "home"
"tell me my gym address"             -> intent: GET_ADDRESS,    entity: "gym"
"""),
    ("human", """Latest message: {user_input} """)
])

_prompt_traffic_status = ChatPromptTemplate.from_messages([
    ("system", """You are an intent and entity parser.
Analyze the user's message and extract the intent and the place name.

INTENTS:
- GET_TRAFFIC   : traffic conditions, delay, or congestion to a place
- GET_ETA       : time taken, eta, time to reach a place
- GET_DISTANCE  : how far, distance to a place

EXTRACTION RULES:
- Extract the actual place name the user mentions.
- If the user says a referential word like "there", "here", or "it", extract that exact word.
- Never output the word "destination" — output the real place name from the message.

EXAMPLES:
"how is traffic to KIIT"             -> intent: GET_TRAFFIC,  entity: "KIIT"
"how long to reach Cuttack"          -> intent: GET_ETA,      entity: "Cuttack"
"how far is Puri"                    -> intent: GET_DISTANCE, entity: "Puri"
"how is the traffic there"           -> intent: GET_TRAFFIC,  entity: "there"
"""),
    ("human", """Latest message: {user_input} """)
])

_prompt_chitchat = ChatPromptTemplate.from_messages([
    ("system", """You are an intent parser.
Analyze the user's message and extract the intent.

INTENT:
- GET_CHITCHAT: general query, greeting, farewell, jokes, facts
"""),
    ("human", """Latest message: {user_input}""")
])

_llm = ChatOllama(model=MODEL, temperature=0.1, num_predict=100, keep_alive=-1)
_structured_llm = _llm.with_structured_output(Intent)


def parse_intent(identify_domain: dict, text: str, session_id: str):

    try:
        session = conversation_store.get_session(session_id)
        history = session.get_history_text()
        domain = identify_domain.get('domain', {})

        # 1. Map Domain to correct Prompt
        domain_prompt_mapping = {
            "DOMAIN_WEATHER": _prompt_weather,
            "DOMAIN_NAVIGATION": _prompt_navigation,
            "DOMAIN_TRAFFIC_STATUS": _prompt_traffic_status,
            "DOMAIN_MEMORY": _prompt_memory,
            "DOMAIN_CHITCHAT": _prompt_chitchat
        }

        selected_prompt = domain_prompt_mapping.get(domain)
        if not selected_prompt:
            return {"intent": "UNKNOWN", "entity": None}

        # 2. Build and Invoke Chain
        _chain = selected_prompt | _structured_llm

        # only navigation prompt uses {history} — other prompts only accept {user_input}. 
        # Passing history to a prompt that doesn't declare it raises a LangChain KeyError
        # breaking every non-navigation domain.
        if domain == "DOMAIN_NAVIGATION":
            result = cast(Intent, _chain.invoke({"user_input": text, "history": history}))
        else:
            result = cast(Intent, _chain.invoke({"user_input": text}))

        # 3. Process Entities and Session Logic
        intent_name = result.intent
        extracted_entity = result.entity
        entities: dict[str, Any] = {"destination": extracted_entity}
        is_dependent = False

        # Intents that carry a real navigable location — only these update last_location
        LOCATION_INTENTS = {
            "GET_ROUTE", "GET_ALTERNATE_ROUTE",
            "GET_TRAFFIC", "GET_ETA", "GET_DISTANCE",
            "GET_WEATHER"
        }

        if extracted_entity:
            dest_lower = extracted_entity.lower().strip()
            if dest_lower in REFERENCE_WORDS:
                is_dependent = True
                entities["destination"] = None  # Clear "there/it" to prepare for resolution
            else:
                # only persist last_location for location-bearing intents.
                if intent_name in LOCATION_INTENTS:
                    session.last_location = extracted_entity
        else:
            # If no entity extracted but intent requires one, mark as dependent
            if intent_name in LOCATION_INTENTS:
                is_dependent = True

        # 4. Resolve from History
        if is_dependent:
            if session.last_location:
                entities["destination"] = session.last_location
                entities["resolved_from_history"] = True
            else:
                entities["resolution_needed"] = True

        return {
            "intent": intent_name,
            "entities": entities,
            "is_dependent": is_dependent
        }

    except Exception as e:
        logger.error(f"Error in parse_intent: {e}")
        return {"intent": "UNKNOWN", "entities": {}, "error": str(e)}