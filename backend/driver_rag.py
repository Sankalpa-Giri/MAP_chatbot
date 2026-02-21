# driver_rag.py - Memory & RAG System

import uuid
import ollama
import chromadb
from backend.config import OLLAMA_MODEL

# Initialize clients
ollama_client = ollama.Client()
chroma_client = chromadb.PersistentClient(path="embeddings_data")
collection = chroma_client.get_or_create_collection(name="driver_collection")

LOCATION_TYPES = ["home", "office", "gym", "work"]

# ==========================================
# MEMORY OPERATIONS
# ==========================================

def handle_memory_ops(user_text: str) -> str | None:
    """Handle remember/forget commands"""
    text_lower = user_text.lower().strip()

    # REMEMBER
    if "remember" in text_lower:
        memory_text = text_lower.split("remember", 1)[1].strip()
        memory_text = memory_text.replace("that", "").strip()

        if memory_text:
            # Detect which location type is being saved
            location_type = None
            for loc in LOCATION_TYPES:
                if f"my {loc}" in memory_text or f"{loc} is" in memory_text:
                    location_type = loc
                    break

            # ── Delete OLD entry for this exact type using metadata filter ──
            if location_type:
                print(f"🔄 Updating {location_type}...")
                try:
                    # Get ALL docs with this exact type tag
                    existing = collection.get(
                        where={"type": location_type}
                    )
                    if existing and existing.get("ids"):
                        for old_id in existing["ids"]:
                            collection.delete(ids=[old_id])
                            print(f"   🗑️ Deleted old {location_type} entry: {old_id}")
                except Exception as e:
                    print(f"   ⚠️ Delete error: {e}")

            # ── Save new memory with exact type tag ────────────────────────
            collection.add(
                ids=[str(uuid.uuid4())],
                documents=[memory_text],
                metadatas=[{
                    "source": "user_memory",
                    "type": location_type or "general"
                }]
            )

            if location_type:
                return f"Updated your {location_type} address."
            else:
                return "Got it. I'll remember that."

        return "What should I remember?"

    # FORGET
    if text_lower.startswith("forget") or text_lower.startswith("delete"):
        topic = text_lower.replace("forget", "").replace("delete", "").strip()

        # Try exact type match first
        for loc in LOCATION_TYPES:
            if loc in topic:
                try:
                    existing = collection.get(where={"type": loc})
                    if existing and existing.get("ids"):
                        for old_id in existing["ids"]:
                            collection.delete(ids=[old_id])
                        return f"Okay, I've forgotten your {loc}."
                except Exception as e:
                    print(f"⚠️ Forget error: {e}")

        # Fallback to fuzzy search
        if topic:
            results = collection.query(query_texts=[topic], n_results=1)
            if results.get("ids") and results["ids"][0]:
                collection.delete(ids=[results["ids"][0][0]])
                return f"Okay, I've forgotten about {topic}."

        return "I couldn't find that memory."

    return None

# ==========================================
# RAG RETRIEVAL — exact match for location types
# ==========================================

def retrieve_context(query: str) -> str:
    """
    Retrieve memory — uses exact metadata filter for location types
    (home/office/gym/work) to avoid cross-contamination.
    Falls back to vector search for general queries.
    """
    try:
        query_lower = query.lower().strip()

        # ── Exact match for known location types ──────────────────────────
        for loc in LOCATION_TYPES:
            if loc in query_lower:
                existing = collection.get(where={"type": loc})
                if existing and existing.get("documents") and existing["documents"]:
                    doc = existing["documents"][0]
                    print(f"   🎯 Exact memory match for '{loc}': {doc}")
                    return f"- {doc}"
                else:
                    return "No memory found."

        # ── Fuzzy vector search for general queries ────────────────────────
        results = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents"]
        )
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "No memory found."
        return "\n".join(f"- {doc}" for doc in docs)

    except Exception as e:
        print(f"⚠️ Retrieve error: {e}")
        return "No memory found."

def query_chroma(query: str) -> str:
    """Alias for compatibility"""
    return retrieve_context(query)

# ==========================================
# LLM INTERACTION
# ==========================================

def build_prompt(query, context, history):
    history_str = "\n".join(history[-3:])
    return f"""You are a Driver Assistant. Be brief.

MEMORY:
{context}

RECENT CONVERSATION:
{history_str}

QUESTION: {query}

Answer in ONE short sentence."""

def ask_llm(user_query: str, history=None) -> str:
    if history is None:
        history = []

    try:
        context = retrieve_context(user_query)
        prompt = build_prompt(user_query, context, history)

        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
            keep_alive=300
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return "I'm having trouble thinking right now."