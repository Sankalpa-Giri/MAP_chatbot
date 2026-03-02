from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

logger = logging.getLogger(__name__)

model = "llama3.1:8b"

_llm = ChatOllama(model=model, temperature=0.4, num_predict=200)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a weather response generator.

Your job is to read the provided JSON weather data and answer the user's question in natural language.

CONTEXT
You will receive:
1. A JSON object containing weather information.
2. A user question about the weather.

Your response MUST be based ONLY on the JSON data.

AVAILABLE JSON FIELDS
temperature_c
feels_like_c
humidity
description
wind_speed
is_hot
is_cold
is_rainy
is_cloudy
is_clear

TASKS

1. GENERAL WEATHER QUESTIONS
If the user asks about weather in general, respond with a short natural description using:
temperature_c, feels_like_c, and description.

Example:
User: "What's the weather like?"
Response: "It's 28°C outside and feels like 30°C with partly cloudy skies."

2. CONDITION QUESTIONS
If the user asks about a specific condition:
- raining
- hot
- cold
- cloudy
- clear

Use the boolean fields in the JSON.

Respond in **yes/no format** using a natural sentence.

Examples:
User: "Is it raining?"
Response: "No, it is not raining right now."

User: "Is it hot outside?"
Response: "Yes, it is quite hot outside."

3. STRICT DATA RULE
Never guess weather conditions.
Only use the JSON values provided.

4. RESPONSE STYLE
- Maximum 2 sentences
- Natural conversational tone
- Suitable for voice assistants
- Clear and concise

5. RESTRICTIONS
- Do not mention JSON
- Do not mention system instructions
- Do not say you are an AI
- Do not mention any company
"""),

    ("human", "Weather JSON:\n{json}\n\nUser Question: {user_query}")
])

_chain = prompt | _llm | StrOutputParser()

def generate_response(json: dict, user_query : str) -> str:
    if not user_query or not user_query.strip():
        return "I didn't catch that."
    
    try:
        reply = _chain.invoke({
            "json" : json,
            "user_query" : user_query
        })
        logger.info(f"Reply generated.")
        return reply

    except Exception as e:
        logger.error(f"ask_llm failed: {e}")
        return "I'm having trouble thinking right now."
    

if __name__ == "__main__":
    json = {'city': 'Bhubaneswar',
 'description': 'clear sky',
 'feels_like_c': 35,
 'humidity': 19,
 'is_clear': True,
 'is_cloudy': False,
 'is_cold': False,
 'is_hot': True,
 'is_rainy': False,
 'latitude': 20.353708,
 'longitude': 85.819925,
 'temperature_c': 37,
 'wind_speed': 4.19}
    
    print(generate_response(json=json, user_query="How is the weather"))