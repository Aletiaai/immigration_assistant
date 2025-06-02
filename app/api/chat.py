from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
from app.models.chat import ChatMessage, ChatResponse, ChatHistory
from app.services.rag_service import RAGService
from app.core.config import MAX_MESSAGES_PER_SESSION
from app.core.dependencies import get_rag_service

router = APIRouter()

# In-memory chat storage (replace with database for production)
chat_sessions: Dict[str, List[ChatHistory]] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, session_id: str = "default", service: RAGService = Depends(get_rag_service)):

    try:
        # Get chat history for this session
        history = chat_sessions.get(session_id, [])
        
        # Convert history to format expected by RAG service
        history_for_rag = [
            {"question": h.question, "response": h.response} 
            for h in history
        ]
        
        # Query RAG system
        result = service.query(message.message, history_for_rag)
        
        # Create response
        response = ChatResponse(
            response=result["response"],
            sources=result["sources"],
            language=result["language"],
            timestamp=datetime.now()
        )
        
        # Store in chat history
        chat_history = ChatHistory(
            question=message.message,
            response=result["response"],
            sources=result["sources"],
            timestamp=datetime.now()
        )
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        chat_sessions[session_id].append(chat_history)
        
        # Keep only last MAX_MESSAGES_PER_SESION number of messages per session defined in app/core/config.py
        if len(chat_sessions[session_id]) > MAX_MESSAGES_PER_SESSION:
            chat_sessions[session_id] = chat_sessions[session_id][-MAX_MESSAGES_PER_SESSION:]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = chat_sessions.get(session_id, [])
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        return {"message": "Chat history cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")