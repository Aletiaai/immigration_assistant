# Path: app/models/chat.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Model for a standard user chat message."""
    message: str
    session_id: str 
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    """Model for a standard chatbot response."""
    response: str
    sources: List[Dict[str, Any]] = []
    language: str
    timestamp: datetime

class ChatHistory(BaseModel):
    """Model for storing a single turn of conversation in the session history."""
    question: str
    response: str
    sources: List[Dict[str, Any]] = []
    timestamp: datetime

class DocumentUpload(BaseModel):
    """Model for the response after uploading a document to the knowledge base."""
    filename: str
    status: str
    message: Optional[str] = None
    timestamp: datetime

class DocumentUploadMessage(BaseModel):
    """Model for a user message that is sent along with a document upload."""
    message: str
    document_file: str  # The filename
    instructions: Optional[str] = None
    timestamp: Optional[datetime] = None

class DocumentProcessingResponse(BaseModel):
    """Model for the initial response after a user uploads a document for a chat session."""
    response: str
    document_filename: str
    processing_status: str
    sources: List[Dict[str, Any]] = []
    language: str
    timestamp: datetime