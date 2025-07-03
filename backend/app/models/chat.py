from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    file_id: str
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatSource(BaseModel):
    page: int
    chunk_id: str
    content: str
    relevance_score: float

class ChatResponse(BaseModel):
    message: str
    sources: List[ChatSource]
    tokens_used: Optional[int] = None