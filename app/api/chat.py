from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any
from datetime import datetime
from app.models.chat import ChatMessage, ChatResponse, ChatHistory, DocumentUploadMessage, DocumentProcessingResponse
from app.services.rag_service import RAGService
from app.core.config import MAX_MESSAGES_PER_SESSION
from app.core.dependencies import get_rag_service
import tempfile
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory chat storage (replace with database for production)
chat_sessions: Dict[str, List[ChatHistory]] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, session_id: str = "default", service: RAGService = Depends(get_rag_service)):
    try:
        # Get chat history for this session
        history = chat_sessions.get(session_id, [])
        logger.info(f"--- ChatEndpoint: Retrieved history for session {session_id}, {len(history)} messages ---")
        
        # Convert history to format expected by RAG service
        history_for_rag = [
            {"question": h.question, "response": h.response} 
            for h in history
        ]
        logger.debug(f"--- ChatEndpoint: History for RAG: {history_for_rag} ---")
        
        # Query RAG system
        result = service.query(message.message, history_for_rag)
        logger.info(f"--- ChatEndpoint: RAG query result: {result} ---")
        
        # Validate result structure
        if not isinstance(result, dict):
            logger.error(f"--- ChatEndpoint: RAG result is not a dictionary: {type(result)} ---")
            raise ValueError("Invalid response type from RAG service")
        required_keys = ["response", "sources", "language"]
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            logger.error(f"--- ChatEndpoint: Missing required keys in RAG result: {missing_keys}, result: {result} ---")
            raise ValueError(f"Missing required keys in RAG result: {missing_keys}")
        if not isinstance(result["response"], str):
            logger.error(f"--- ChatEndpoint: Response is not a string: {type(result['response'])}, value: {result['response']} ---")
            raise ValueError("Response must be a string")
        if not isinstance(result["sources"], list):
            logger.error(f"--- ChatEndpoint: Sources is not a list: {type(result['sources'])}, value: {result['sources']} ---")
            raise ValueError("Sources must be a list")
        if not isinstance(result["language"], str):
            logger.error(f"--- ChatEndpoint: Language is not a string: {type(result['language'])}, value: {result['language']} ---")
            raise ValueError("Language must be a string")
        
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
        
        # Keep only last MAX_MESSAGES_PER_SESSION number of messages
        if len(chat_sessions[session_id]) > MAX_MESSAGES_PER_SESSION:
            chat_sessions[session_id] = chat_sessions[session_id][-MAX_MESSAGES_PER_SESSION:]
        
        logger.info(f"--- ChatEndpoint: Response prepared for query: {message.message} ---")
        return response
        
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Error processing chat: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = chat_sessions.get(session_id, [])
        logger.info(f"--- ChatEndpoint: Retrieved history for session {session_id}, {len(history)} messages ---")
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to retrieve chat history: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"--- ChatEndpoint: Cleared chat history for session {session_id} ---")
        return {"message": "Chat history cleared", "session_id": session_id}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to clear chat history: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")

@router.post("/chat/document", response_model=DocumentProcessingResponse)
async def process_document_with_chat(
    file: UploadFile = File(...),
    message: str = Form(...),
    instructions: str = Form(default=""),
    session_id: str = Form(default="default"),
    service: RAGService = Depends(get_rag_service)
):
    try:
        # Validate file type
        if not (file.filename.lower().endswith('.pdf') or file.filename.lower().endswith('.docx')):
            raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported")
        
        # Create temporary file with appropriate suffix
        suffix = '.pdf' if file.filename.lower().endswith('.pdf') else '.docx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process document temporarily, passing the original filename
            result = service.process_document_temporarily(temp_file_path, file.filename, message, instructions)
            logger.info(f"--- ChatEndpoint: Document processed: {file.filename}, result: {result} ---")
            
            return DocumentProcessingResponse(
                response=result["response"],
                document_filename=file.filename,
                processing_status="completed",
                sources=result.get("sources", []),
                language=result.get("language", "en"),
                timestamp=datetime.now()
            )
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Document processing failed: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")