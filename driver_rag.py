# driver_rag.py
import uuid
import logging
import chromadb
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

# ==========================================
# CONFIG
# ==========================================

LLM_MODEL = "llama3.1:8b"
EMBED_MODEL = "nomic-embed-text"

# ==========================================
# CHROMA — persistent vector memory
# ==========================================

_chroma_client = chromadb.PersistentClient(path="driver_memory")
_collection = _chroma_client.get_or_create_collection(name="driver_collection")

# ==========================================
# EMBEDDINGS — via LangChain/Ollama
# ==========================================

_embedder = OllamaEmbeddings(model=EMBED_MODEL)

def _get_embedding(text: str) -> list[float]:
    return _embedder.embed_query(text)

# ==========================================
# LLM CHAIN
# ==========================================

_llm = ChatOllama(model=LLM_MODEL, temperature=0.4, num_predict=200)

_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are DriverAI — an intelligent in-car assistant in Bhubaneswar, India.

PERSONALITY:
- Smart, helpful, calm
- Speak naturally and concisely — this is a voice response, max 2 sentences
- Never mention being an AI or your model name unless directly asked
- Never say you are built by any company

RULES:
1. If the answer exists in MEMORY → use it, prioritize it over general knowledge
2. If not in memory → answer from general knowledge
3. For personal info not in memory → say "I don't know that yet"
"""),
    ("human", "MEMORY:\n{memory_context}\n\nQuestion: {user_query}")
])

_rag_chain = _prompt | _llm | StrOutputParser()

# ==========================================
# MEMORY STORE
# ==========================================

def store_memory(user_text: str) -> dict | None:
    """
    Stores memory if text starts with 'remember'.
    Returns status dict if triggered, None if not applicable.
    Called by chatbot_brain before ask_llm — not repeated inside ask_llm.
    """
    if not user_text.lower().startswith("remember"):
        return None

    memory_text = user_text[len("remember"):].strip()
    if not memory_text:
        return {
            "reply": "What would you like me to remember?",
            "action": "CLARIFY",
            "data": {}
        }

    try:
        emb = _get_embedding(memory_text)
        _collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[emb],
            documents=[memory_text],
            metadatas=[{"type": "memory"}]
        )
        logger.info(f"Memory stored: '{memory_text}'")
        return {
            "reply": f"Got it, I'll remember that.",
            "action": "REPLY",
            "data": {"stored": memory_text}
        }
    except Exception as e:
        logger.error(f"store_memory failed: {e}")
        return {
            "reply": "I couldn't save that to memory.",
            "action": "ERROR",
            "data": {}
        }

# ==========================================
# MEMORY DELETE
# ==========================================

def delete_memory(user_text: str) -> dict | None:
    """
    Deletes closest memory match if text starts with 'delete' or 'forget'.
    Returns status dict if triggered, None if not applicable.
    """
    text_lower = user_text.lower()
    trigger = next(
        (t for t in ("forget", "delete") if text_lower.startswith(t)),
        None
    )
    if not trigger:
        return None

    topic = user_text[len(trigger):].strip()
    if not topic:
        return {
            "reply": "What would you like me to forget?",
            "action": "CLARIFY",
            "data": {}
        }

    try:
        emb = _get_embedding(topic)
        results = _collection.query(query_embeddings=[emb], n_results=1)

        if not results["ids"] or not results["ids"][0]:
            return {
                "reply": f"I don't have anything stored about {topic}.",
                "action": "REPLY",
                "data": {}
            }

        _collection.delete(ids=[results["ids"][0][0]])
        logger.info(f"Memory deleted for topic: '{topic}'")
        return {
            "reply": f"Done, I've forgotten that.",
            "action": "REPLY",
            "data": {"deleted_topic": topic}
        }
    except Exception as e:
        logger.error(f"delete_memory failed: {e}")
        return {
            "reply": "I couldn't delete that from memory.",
            "action": "ERROR",
            "data": {}
        }

# ==========================================
# MEMORY RETRIEVE
# ==========================================

def retrieve_memory(query: str) -> str:
    """
    Returns relevant memory context as a plain string.
    Used internally by ask_llm and externally by chatbot_brain
    for shortcut location resolution.
    """
    if not query or not query.strip():
        return ""

    try:
        emb = _get_embedding(query)
        results = _collection.query(
            query_embeddings=[emb],
            n_results=3,
            include=["documents"]
        )
        documents = results.get("documents") or [[]]  # handles None explicitly
        docs = documents[0] if documents else []
        return "\n".join(docs) if docs else ""
    except Exception as e:
        logger.error(f"retrieve_memory failed: {e}")
        return ""

# ==========================================
# ASK LLM
# ==========================================

def ask_llm(user_query: str) -> dict:
    """
    Pure LLM query with RAG context injection.
    Memory store/delete are NOT handled here — chatbot_brain
    calls store_memory/delete_memory separately before routing here,
    so this function only runs for UNKNOWN intents that reach the LLM.
    """
    if not user_query or not user_query.strip():
        return {
            "reply": "I didn't catch that.",
            "action": "ERROR",
            "data": {}
        }

    try:
        memory_context = retrieve_memory(user_query)

        reply = _rag_chain.invoke({
            "memory_context": memory_context or "No stored memory.",
            "user_query": user_query
        })

        logger.info(f"RAG reply generated. Memory used: {bool(memory_context)}")

        return {
            "reply": reply,
            "action": "REPLY",
            "data": {"memory_used": bool(memory_context)}
        }

    except Exception as e:
        logger.error(f"ask_llm failed: {e}")
        return {
            "reply": "I'm having trouble thinking right now.",
            "action": "ERROR",
            "data": {}
        }

# ==========================================
# TERMINAL TEST
# ==========================================

if __name__ == "__main__":
    print("🚗 DriverAI Started (type 'exit' to quit)\n")
    while True:
        q = input("You: ").strip()
        if q.lower() == "exit":
            break
        
        # Test memory ops first
        result = store_memory(q) or delete_memory(q) or ask_llm(q)
        print(f"AI: {result['reply']}\n")