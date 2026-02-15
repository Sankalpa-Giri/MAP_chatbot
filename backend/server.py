from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Annotated
import main

app = FastAPI(title="AudiBOT")



# ==========================================
# 2. DATA MODELS
# ==========================================

class VoiceCommand(BaseModel):
    text: Annotated[str, Field(..., description="Text to be processed by LLM")]

# ==========================================
# 4. API ENDPOINTS
# ==========================================
@app.get('/')
async def start_page():
    return "Welcome to AudiBOT"


@app.post('/voice')
async def voice(request : VoiceCommand):
    
    try:
        main_response = main.handle_user_input(request.text)

        return main_response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
