import logging
import chromadb
from langchain_ollama import OllamaEmbeddings
from config import EMBED_MODEL

logger = logging.getLogger(__name__)

# ==========================================
# CHROMA — persistent vector memory
# ==========================================

_chroma_client = chromadb.PersistentClient(path="driver_memory")
_collection = _chroma_client.get_or_create_collection(name="driver_collection")

# ==========================================
# EMBEDDINGS
# ==========================================

_embedder = OllamaEmbeddings(model=EMBED_MODEL)

def _get_embedding(text: str) -> list[float]:
    return _embedder.embed_query(text)


# ==========================================
# MEMORY STORE
# ==========================================

def store_memory(user_address: dict) -> dict:

    if not user_address.get("location"):
        return {"reply": "Say an address to remember"}

    label = user_address["label"]
    location = user_address["location"]

    memory_text = f"{label}: {location}"

    try:
        emb = _get_embedding(memory_text)

        _collection.add(
            ids=[label],
            embeddings=[emb],
            documents=[location],
            metadatas=[{
                "type": "address",
                "label": label,
                "location": location
            }]
        )

        logger.info(f"Memory stored: '{memory_text}'")

        return {
            "reply": f"Got it. I'll remember your {label} address.",
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
# MEMORY UPDATE
# ==========================================

def update_memory(user_address: dict) -> dict:
    """
    Updates an existing address entry identified by label.

    Uses ChromaDB's update() which requires the document to already exist —
    unlike upsert(), this lets us give a clear 'not found' reply instead of
    silently creating a new entry when the user intended to update an old one.

    Parameters:
        user_address: {"label": str, "location": str}

    Returns:
        Standard reply dict with "reply", "action", "data" keys.
    """
    if not user_address.get("location"):
        return {
            "reply": "Please provide the new address to update.",
            "action": "CLARIFY",
            "data": {}
        }

    label = user_address["label"]
    location = user_address["location"]
    memory_text = f"{label}: {location}"

    try:
        # Check the label exists before attempting update — update() on a
        # missing ID silently does nothing, which would give a false success reply.
        existing = _collection.get(ids=[label])
        if not existing["ids"]:
            return {
                "reply": f"I don't have a {label} address saved yet. Say 'save my {label}' to add one.",
                "action": "CLARIFY",
                "data": {"missing_label": label}
            }

        emb = _get_embedding(memory_text)

        _collection.update(
            ids=[label],
            embeddings=[emb],
            documents=[location],
            metadatas=[{
                "type": "address",
                "label": label,
                "location": location
            }]
        )

        logger.info(f"Memory updated: '{memory_text}'")

        return {
            "reply": f"Done, I've updated your {label} address.",
            "action": "REPLY",
            "data": {"updated": memory_text}
        }

    except Exception as e:
        logger.error(f"update_memory failed: {e}")
        return {
            "reply": "I couldn't update that in memory.",
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
    trigger = next((t for t in ("forget", "delete") if text_lower.startswith(t)), None)
    if not trigger:
        return None

    topic = user_text[len(trigger):].strip()
    if not topic:
        return {
            "reply": "What would you like me to delete?",
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
        results = _collection.query(query_embeddings=[emb], n_results=3, include=["documents"])
        documents = results.get("documents") or [[]]  # handles None explicitly
        docs = documents[0] if documents else []
        return "\n".join(docs) if docs else ""
    except Exception as e:
        logger.error(f"retrieve_memory failed: {e}")
        return ""