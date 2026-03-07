from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import MODEL

_general_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful voice assistant for drivers.
Answer the user's question in a friendly and optimistic manner.
Be concise and practical. Avoid long paragraphs — this is a voice response.
Never say you are an AI or mention your model name."""),
    ("human", """ user text: {user_text} """)
])

_llm = ChatOllama(model=MODEL, temperature=0.6, num_predict=200,keep_alive=-1)
_chain = _general_prompt | _llm | StrOutputParser()

def chat(text: str):
    if not text or not text.strip():
        return {
            "reply" : "Could you say that again?"
        }
    try:
        result = _chain.invoke({"user_text" : text})
        return {
            "reply": result
        }
    
    except Exception as e:
        return{
            "reply" : "Ollama Offline"
        }


if __name__ == "__main__":
    text = "different colours in traffic lights"
    reply = chat(text)
    print(reply.get('reply'))