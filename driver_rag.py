import uuid
import ollama
import chromadb

OLLAMA_MODEL = "phi3:mini"

ollama_client = ollama.Client()
chroma_client = chromadb.PersistentClient(path="embeddings_data")
collection = chroma_client.get_or_create_collection(name="driver_collection")

def handle_memory_ops(user_text: str) -> str | None:
    """Handle remember/forget commands with smart updates"""
    text_lower = user_text.lower().strip()
    
    # Remember command with AUTO-UPDATE
    if "remember" in text_lower:
        memory_text = text_lower.split("remember", 1)[1].strip()
        memory_text = memory_text.replace("that", "").strip()
        
        if memory_text:
            # Check if updating home/office/gym
            location_type = None
            for loc in ["home", "office", "gym", "work"]:
                if f"my {loc}" in memory_text or f"{loc} is" in memory_text:
                    location_type = loc
                    break
            
            # Delete old memory if updating
            if location_type:
                print(f"🔄 Updating {location_type} address...")
                old_results = collection.query(query_texts=[f"{location_type}"], n_results=5)
                
                if old_results.get("ids") and old_results["ids"][0]:
                    # Delete all old entries for this location
                    for old_id in old_results["ids"][0]:
                        try:
                            collection.delete(ids=[old_id])
                            print(f"🗑️ Deleted old {location_type} memory")
                        except:
                            pass
            
            # Add new memory
            collection.add(
                ids=[str(uuid.uuid4())],
                documents=[memory_text],
                metadatas=[{"source": "user_memory", "type": location_type or "general"}]
            )
            print(f"💾 Saved: {memory_text}")
            
            if location_type:
                return f"Updated your {location_type} address."
            else:
                return f"Got it. I'll remember that."
        
        return "What should I remember?"
    
    # Forget command
    if text_lower.startswith("forget") or text_lower.startswith("delete"):
        topic = text_lower.replace("forget", "").replace("delete", "").strip()
        if topic:
            results = collection.query(query_texts=[topic], n_results=1)
            if results.get("ids") and results["ids"][0]:
                collection.delete(ids=[results["ids"][0][0]])
                return f"Okay, I've forgotten about {topic}."
        return "I couldn't find that memory."
    
    return None

def retrieve_context(query: str) -> str:
    """Retrieve relevant memory"""
    try:
        results = collection.query(query_texts=[query], n_results=3, include=["documents"])
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "No memory found."
        return "\n".join(f"- {doc}" for doc in docs)
    except:
        return "No memory found."

def query_chroma(query: str) -> str:
    """Alias for compatibility"""
    return retrieve_context(query)

def build_prompt(query, context, history):
    history_str = "\n".join(history[-3:])
    return f"""You are a Driver Voice Assistant. Be brief.

MEMORY:
{context}

RECENT CONVERSATION:
{history_str}

QUESTION: {query}

Answer in ONE short sentence."""

def ask_llm(user_query: str, history=None) -> str:
    """Query LLM with context"""
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