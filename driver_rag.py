import ollama
import chromadb
import uuid

OLLAMA_FLASH_ATTENTION = True
ollama_client = ollama.Client()
chroma_client = chromadb.PersistentClient(path='embeddings data')
#chroma_client.delete_collection(name = "driver_collection")
collection = chroma_client.get_or_create_collection(name="driver_collection")

def query_chroma(query):
    result = collection.query(
        query_texts=[query], 
        n_results=3, 
        include=["documents"])

    # safeguard: if no results
    if result["documents"] is None or len(result["documents"][0]) == 0:
        return "No relevant memory found."

    # return the top document
    formatted_memories = "\n".join([f"- {doc}" for doc in result["documents"][0]])
    return formatted_memories

def store_memory(query):
    words = query.split()

    if words[0].lower() == "remember":
        # Extract the fact (everything after 'remember')
        memory_text = " ".join(words[1:])  # KEEP spaces

        if not memory_text:
            return "What should I remember?"
        
        # Generate a unique ID to avoid overwriting
        unique_id = str(uuid.uuid4())

        collection.add(
            ids=[unique_id],
            documents=[memory_text],
            metadatas=[{"source": "user_memory"}]
        )

        return "Information has been stored."

    return None

def delete_memory(query):
    query = query.strip()
    # Trigger if user says "Delete [topic]"
    if query.lower().startswith("delete"):
        topic = query[7:].strip()
        
        # 1. Search for the most relevant record to delete
        results = collection.query(
            query_texts=[topic],
            n_results=1
        )
        
        if not results["ids"] or len(results["ids"][0]) == 0:
            return "I couldn't find any memory related to that."

        # 2. Get the ID and the content of what we're about to delete
        target_id = results["ids"][0][0]
        #target_text = results["documents"][0][0]
        
        # 3. Perform the deletion
        collection.delete(ids=[target_id])
        
        return f"Memory cleared."
    
    return None

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
    return prompt



def ask_llm(user_query):

    # 1. Get context
    context = query_chroma(user_query)
    #print(f"\n[DEBUG] RETRIEVED:\n{context}\n")

    # 2. Build Prompt
    prompt = build_prompt(user_query, context)

    # 3. Call Ollama
    response = ollama_client.chat(
        model="phi3:mini",   # Replace anytime with Phi, Qwen, Mistral
        messages=[
            {"role": "system", "content": "You are a concise assistant that only answers based on provided memory."},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0},
        keep_alive=300
    )
    return response["message"]["content"]

#Main function
if __name__ == '__main__':
    while True:
        user_query = input("You: ").strip()

        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # 1. Try to store memory
        memory_resp = store_memory(user_query)
        if memory_resp:
            print("Assistant:", memory_resp)
            continue

        # 2. Try to forget memory
        forget_resp = delete_memory(user_query)
        if forget_resp:
            print(f"Assistant: {forget_resp}")
            continue

        answer = ask_llm(user_query)
        print("Assistant: ",answer)