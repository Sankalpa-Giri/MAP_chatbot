import uuid
import ollama
import chromadb

# ==========================================
# 1. MODEL CONFIG
# ==========================================

LLM_MODEL = "llama3.1:8b"
EMBED_MODEL = "nomic-embed-text"

ollama_client = ollama.Client()

# persistent memory
chroma_client = chromadb.PersistentClient(path="driver_memory")
collection = chroma_client.get_or_create_collection(name="driver_collection")

# ==========================================
# 2. EMBEDDING FUNCTION (USING NOMIC)
# ==========================================

def get_embedding(text: str):
    response = ollama_client.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )
    return response["embedding"]

# ==========================================
# 3. MEMORY STORE
# ==========================================

def store_memory(user_text: str):
    if not user_text.lower().startswith("remember"):
        return None

    memory_text = user_text[len("remember"):].strip()
    if not memory_text:
        return {"error": "EMPTY_MEMORY"}

    emb = get_embedding(memory_text)

    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[emb],
        documents=[memory_text],
        metadatas=[{"type": "memory"}]
    )

    return {"status": "MEMORY STORED", "content": memory_text}

# ==========================================
# 4. MEMORY DELETE
# ==========================================

def delete_memory(user_text: str):
    if not user_text.lower().startswith("delete"):
        return None

    topic = user_text[len("delete"):].strip()
    if not topic:
        return {"error": "NO_TOPIC"}

    emb = get_embedding(topic)

    results = collection.query(
        query_embeddings=[emb],
        n_results=1
    )

    if not results["ids"] or not results["ids"][0]:
        return {"error": "NOT FOUND"}

    collection.delete(ids=[results["ids"][0][0]])
    return {"status": "DELETED", "topic": topic}

# ==========================================
# 5. MEMORY RETRIEVE
# ==========================================

def retrieve_memory(query: str):
    emb = get_embedding(query)

    results = collection.query(
        query_embeddings=[emb],
        n_results=3,
        include=["documents"]
    )

    docs = results.get("documents", [[]])[0]
    if not docs:
        return "No stored memory."

    return "\n".join(docs)

# ==========================================
# 6. PROMPT BUILDER
# ==========================================

def build_prompt(user_query, memory_context):

    return f"""
You are DriverAI — an intelligent in-car driver assistant.

PERSONALITY:
- Smart
- Helpful
- Calm
- Speak naturally
- Never say you are built by Microsoft or any company
- Never mention being an AI model unless asked

MEMORY (Highest Priority):
{memory_context}

RULES:
1. If answer exists in MEMORY → use it
2. If not → answer normally using knowledge
3. For personal info not in memory → say "I don't know that yet"
4. Keep answers concise (max 2 lines)
5. Act like a real car assistant

USER QUESTION:
{user_query}

ASSISTANT:
"""

# ==========================================
# 7. ASK LLM
# ==========================================

def ask_llm(user_query: str):

    # store memory
    mem_store = store_memory(user_query)
    if mem_store:
        return mem_store

    # delete memory
    mem_delete = delete_memory(user_query)
    if mem_delete:
        return mem_delete

    # retrieve memory
    context = retrieve_memory(user_query)

    prompt = build_prompt(user_query, context)

    try:
        response = ollama_client.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are DriverAI, a smart in-car assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.4,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        )

        reply = response["message"]["content"].strip()

        return {
            "reply": reply,
            "memory_used": context != "No stored memory."
        }

    except Exception as e:
        return {
            "error": str(e)
        }

# ==========================================
# 8. TERMINAL CHAT LOOP (TEST)
# ==========================================

if __name__ == "__main__":
    print("🚗 Driver AI Assistant Started (type 'exit' to quit)\n")

    while True:
        q = input("You: ")

        if q.lower() == "exit":
            break

        result = ask_llm(q)
        print("AI:", result)
