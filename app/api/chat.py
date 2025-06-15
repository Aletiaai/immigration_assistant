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

# In-memory storage now holds session objects containing both history and document context.
chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieves or creates a chat session object. A session contains 'history' and 'document_context'."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "history": [],
            "document_context": None
        }
    return chat_sessions[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, session_id: str = "default", service: RAGService = Depends(get_rag_service)):
    """It checks for topic changes within a document chat session."""
    try:
        # Get chat history for this session
        session = get_session(session_id)        
        # Convert history to format expected by RAG service
        history_for_rag = [
            {"question": h.question, "response": h.response} 
            for h in session["history"]
        ]

        query_general_kb = False # Flag to decide which RAG method to call

        logger.debug(f"--- ChatEndpoint: History for RAG: {history_for_rag} ---")

        # Check if there is a document context in the current session
        if session.get("document_context"):
            logger.info(f"--- ChatEndpoint: Found document context for session {session_id}. Querying against document. ---")
            # A document is in context. Check if this is a follow-up or a new topic.
            is_follow_up = service.is_topic_follow_up(message.message, history_for_rag)
            if is_follow_up:
                logger.info(f"--- ChatEndpoint: Follow-up question detected for session {session_id}. Querying document. ---")
                result = service.query_with_context(
                    question=message.message,
                    chat_history=history_for_rag,
                    document_chunks=session["document_context"]["chunks"]
                )
            else:
                # The user changed the topic. Query the general KB instead.
                logger.info(f"--- ChatEndpoint: New topic detected for session {session_id}. Querying general KB. ---")
                query_general_kb = True

        else:
            # No document in context, so always query the general KB
            query_general_kb = True

        if query_general_kb:
            result = service.query(message.message, history_for_rag)
        
        # Create response
        response = ChatResponse(
            response = result["response"],
            sources = result.get("sources",[]),
            language=result.get("language", "en"),
            timestamp = datetime.now()
        )
        
        # Update session history
        session["history"].append(ChatHistory(
            question = message.message,
            response = response.response,
            sources = response.sources,
            timestamp = response.timestamp
        ))
        
        logger.info(f"--- ChatEndpoint: Response prepared for query: {message.message} ---")
        return response
        
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Error processing chat: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    # This endpoint can be used for debugging or retrieving session data
    try:
        session = get_session(session_id)
        logger.info(f"--- ChatEndpoint: Retrieved history for session {session_id}, {len(session)} messages ---")
        return {"session_id": session_id, "history": session}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to retrieve chat history: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clears all data for a session, including history and document context."""
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"--- ChatEndpoint: Cleared all data for session {session_id} ---")
        return {"message": "Chat history and document context cleared", "session_id": session_id}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to clear chat history: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")

@router.post("/chat/document", response_model=DocumentProcessingResponse)
async def upload_and_chat(
    file: UploadFile = File(...),
    message: str = Form(...),
    session_id: str = Form("default"),
    service: RAGService = Depends(get_rag_service)
):
    """This endpoint calls 'start_document_chat' to initiate a multi-turn document conversation."""
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
            result, processed_chunks = service.start_document_chat(file_path = temp_file_path, question = message)
            logger.info(f"--- ChatEndpoint: Document processed: {file.filename}, result: {result} ---")
            
            # Store the processed chunks in the user's session for follow-up questions
            session = get_session(session_id)
            session["document_context"] = {"filename": file.filename,"chunks": processed_chunks}
            logger.info(f"--- ChatEndpoint: Document context for '{file.filename}' stored in session {session_id}. ---")

            # Store this first interaction in the history
            session["history"].append(ChatHistory(
                question = message,
                response = result["response"],
                sources = result.get("sources", []),
                timestamp = datetime.now()
            ))

            return DocumentProcessingResponse(
                response = result["response"],
                document_filename = file.filename,
                processing_status = "completed",
                sources = result.get("sources", []),
                language = result.get("language", "en"),
                timestamp = datetime.now()
            )

        except Exception as e:
            logger.error(f"--- ChatEndpoint: Document chat initiation failed: {e} ---", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {e}")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Document processing failed: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")