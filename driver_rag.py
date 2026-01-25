import uuid
import ollama
import chromadb

# ==========================================
# 1. CLIENT SETUP
# ==========================================

OLLAMA_MODEL = "phi3:mini"

ollama_client = ollama.Client()
chroma_client = chromadb.PersistentClient(path="embeddings_data")
#chroma_client.delete_collection(name = "driver_collection")
collection = chroma_client.get_or_create_collection(name="driver_collection")


# ==========================================
# 2. MEMORY OPERATIONS
# ==========================================

def store_memory(user_text: str) -> dict | None:
    """
    Stores memory if user intent starts with 'remember'.
    """
    words = user_text.strip().split()

    if not words or words[0].lower() != "remember":
        return None

    memory_text = " ".join(words[1:]).strip()
    if not memory_text:
        return {"error": "EMPTY_MEMORY"}

    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[memory_text],
        metadatas=[{"source": "user_memory"}]
    )

    return {"status": "STORED", "content": memory_text}


def delete_memory(user_text: str) -> dict | None:
    """
    Deletes memory if user intent starts with 'delete'.
    """
    if not user_text.lower().startswith("delete"):
        return None

    topic = user_text[6:].strip()
    if not topic:
        return {"error": "NO_TOPIC_PROVIDED"}

    results = collection.query(query_texts=[topic], n_results=1)

    if not results.get("ids") or not results["ids"][0]:
        return {"error": "MEMORY_NOT_FOUND"}

    collection.delete(ids=[results["ids"][0][0]])

    return {"status": "DELETED", "topic": topic}


def retrieve_memory(query: str) -> str:
    """
    Retrieves relevant memory for a query.
    """
    results = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents"]
    )

    docs = results.get("documents", [[]])[0]
    if not docs:
        return "I don't know that yet."

    return "\n".join(f"- {doc}" for doc in docs)


# ==========================================
# 3. PROMPT BUILDER
# ==========================================

def build_prompt(query, context):
    prompt = f"""You are a helpful Driver Voice Assistant. Your goal is to provide concise, accurate information to the driver.

    RULES:
    1. **Priority:** Always check the provided MEMORY first. If the answer is there, use it.
    2. **Fallback:** If the MEMORY does not contain the answer, use your general knowledge to provide a helpful response.
    3. **Safety:** Do not make up personal facts about the user that are not in memory.
    4. **Style:** Keep the answer to ONE short sentence. No code, no analysis, no extra explanations.
    5. For personal details about the user (like name, home, or preferences), only answer if found in MEMORY and reply with 'I don't know that yet' if not in the memory. For general facts, use your own knowledge.

    MEMORY: 
    {context}

    QUESTION: 
    {query}

    FINAL ANSWER:"""




# ==========================================
# 4. LLM QUERY
# ==========================================

def ask_llm(user_query: str) -> dict:
    """
    Queries the LLM with RAG context.
    """
    context = retrieve_memory(user_query)
    prompt = build_prompt(user_query, context)

    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0},
            keep_alive=300
        )

        return {
            "reply": response["message"]["content"],
            "used_memory": context != "I don't know that yet."
        }

    except Exception as e:
        return {
            "error": "LLM_ERROR",
            "details": str(e)
        }
