from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    language: str
    timestamp: datetime

class ChatHistory(BaseModel):
    question: str
    response: str
    sources: List[Dict[str, Any]] = []
    timestamp: datetime

class DocumentUpload(BaseModel):
    filename: str
    status: str
    message: Optional[str] = None
    timestamp: datetime