'''
FastAPI server. Run the command to start the server: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
It has two Data models: ChatRequest and ChatResponse
It has two end points: 
                    "/" - the home/root endpoint. Used to check status of server.
                    "/voice" - API calling end point. It does not enforce any return format, only returns the main_response.
                               Used to interact with the server by request and response of messages.
                    "/docs" - Swagger UI of FastAPI. Used to test API calls.
'''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated, Optional
import main

app = FastAPI(title="Hey Shift")

# ==========================================
# DATA MODELS
# ==========================================

class ChatRequest(BaseModel):
    text: Annotated[str, Field(..., description="Text to be processed by the system")]
    latitude: Annotated[float,Field(None, description="User's current latitude")]
    longitude: Annotated[float,Field(None, description="User's current longitude")]
    session_id: str = Field(default="default", description="Stable ID per user/device session")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Text response to return to the client")
    action: Optional[str] = None
    data: Optional[dict] = None

# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/")
async def start_page():
    return {"message": "Welcome to AudiBOT.", "status": "Running"}


@app.post("/voice", response_model=ChatResponse)
async def voice(request: ChatRequest):
    try:
        text = request.text.strip().lower()

        if not text:
            return ChatResponse(reply="I didn't catch that. Please say again.")

        main_response = main.handle_user_input(user_text=text, latitude=request.latitude, longitude=request.longitude, session_id=request.session_id)

        # main.py guarantees a dict with at least {"reply": str}
        return ChatResponse(
            reply=main_response.get("reply", "No response generated."),
            action=main_response.get("action"),
            data=main_response.get("data")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))