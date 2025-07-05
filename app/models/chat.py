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
<<<<<<< HEAD
    timestamp: datetime

class DocumentUploadMessage(BaseModel):
    message: str
    document_file: str  # filename
    instructions: Optional[str] = None
    timestamp: Optional[datetime] = None

class DocumentProcessingResponse(BaseModel):
    response: str
    document_filename: str
    processing_status: str
    sources: List[Dict[str, Any]] = []
    language: str
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    timestamp: datetime