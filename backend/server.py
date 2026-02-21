# server.py - SHIFT Traffic Assistant Backend

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import traceback

# ── Import your existing modules ──────────────────────────────────────────────
try:
    from backend import nlu_engine
    from backend import chatbot_brain
    from backend import driver_rag
except ImportError as e:
    raise RuntimeError(f"Missing module: {e}")

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="SHIFT Traffic Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session state ─────────────────────────────────────────────────────────────
session = {
    "last_interaction": 0,
    "conversation_active": False,
    "last_destination": None,
}

FOLLOW_UP_WINDOW = 30

# ── Models ────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    reply: str

# ── Main chat endpoint ────────────────────────────────────────────────────────
@app.post("/voice", response_model=ChatResponse)
async def voice_endpoint(req: ChatRequest):
    user_text = req.text.strip()

    if not user_text:
        return ChatResponse(reply="I didn't catch that. Please try again.")

    print(f"\n📱 Android → Server: '{user_text}'")

    try:
        intent      = nlu_engine.parse_intent(user_text)
        intent_type = intent.get("intent", "unknown")
        destination = intent.get("destination")

        print(f"   Intent: {intent_type} | Dest: {destination}")

        if destination:
            session["last_destination"] = destination
        elif intent_type == "get_route_traffic" and not destination:
            if session["last_destination"]:
                intent["destination"] = session["last_destination"]

        if intent_type in ("save_memory", "delete_memory"):
            memory_reply = driver_rag.handle_memory_ops(user_text)
            if memory_reply:
                _update_session()
                return ChatResponse(reply=memory_reply)

        if intent_type == "stop":
            session["conversation_active"] = False
            return ChatResponse(reply="Okay, goodbye! Drive safe.")

        reply = chatbot_brain.get_bot_response(intent, user_text)

        if not reply or reply == "stop_now":
            return ChatResponse(reply="Goodbye! Drive safe.")

        _update_session(destination)
        print(f"   🤖 Reply: {reply}")
        return ChatResponse(reply=reply)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _update_session(destination=None):
    session["last_interaction"] = time.time()
    session["conversation_active"] = True
    if destination:
        session["last_destination"] = destination

@app.get("/")
async def health():
    return {"status": "SHIFT backend running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=7777, reload=True)