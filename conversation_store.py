# conversation_store.py
# Centralized session memory — imported by nlu_engine and chatbot_brain

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Turn:
    role: str           # "user" or "assistant"
    text: str
    intent: Optional[str] = None
    resolved_location: Optional[str] = None  # last known destination/location

@dataclass  
class Session:
    turns: deque = field(default_factory=lambda: deque(maxlen=10))  # last 10 turns
    last_destination: Optional[str] = None
    last_location: Optional[str] = None  # for weather context

    def add_turn(self, role: str, text: str, intent: Optional[str] = None, location: Optional[str] = None):
        self.turns.append(Turn(role=role, text=text, intent=intent, resolved_location=location))
        # Track last known locations across turns
        if location:
            if intent in ("GET_ROUTE", "GET_TRAFFIC", "GET_ALTERNATE_ROUTE"):
                self.last_destination = location
            elif intent == "GET_WEATHER":
                self.last_location = location

    def get_history_text(self) -> str:
        """Formatted history for LLM context."""
        lines = []
        for turn in self.turns:
            prefix = "User" if turn.role == "user" else "Assistant"
            lines.append(f"{prefix}: {turn.text}")
        return "\n".join(lines)

# Single in-memory store — keyed by session_id
# Replace with Redis for multi-user production deployments
_sessions: dict[str, Session] = {}

def get_session(session_id: str) -> Session:
    if session_id not in _sessions:
        _sessions[session_id] = Session()
    return _sessions[session_id]

def clear_session(session_id: str):
    _sessions.pop(session_id, None)