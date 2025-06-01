from fastapi import HTTPException, Depends
from typing import Optional
from app.services.rag_service import RAGService
import logging

logger = logging.getLogger(__name__)

# Global RAG service instance
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    """
    Dependency to get RAG service instance with proper error handling
    """
    global _rag_service
    
    if _rag_service is None:
        try:
            logger.info("Initializing RAG service...")
            _rag_service = RAGService()
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"RAG service initialization failed: {str(e)}"
            )
    
    return _rag_service

def validate_session_id(session_id: str) -> str:
    """
    Validate and sanitize session ID
    """
    try:
        if not session_id or len(session_id.strip()) == 0:
            return "default"
        
        # Remove any potentially harmful characters
        sanitized = "".join(c for c in session_id if c.isalnum() or c in "-_")
        
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
            
        return sanitized or "default"
        
    except Exception as e:
        logger.warning(f"Session ID validation failed: {str(e)}")
        return "default"