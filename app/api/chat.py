<<<<<<< HEAD
# Path: app/api/chat.py

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
import io
import docx
import fitz

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage now holds session objects containing both history and document context.
chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieves or creates a chat session. A session now includes 'history', 'document_context', and a 'mode'."""
    if session_id not in chat_sessions:
        logger.info(f"--- Creating new session: {session_id} ---")
        chat_sessions[session_id] = {
            "history": [],
            "document_context": None,
            "mode": "GENERAL_QA"  # Default mode is general Q&A
        }
    return chat_sessions[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, session_id: str = "default", service: RAGService = Depends(get_rag_service)):
    """ Handles chat messages using a stateful agent model. It uses a router to determine if the query is about a document or the general knowledge base."""
    try:
        # Get chat history for this session
        session = get_session(session_id)        
        # Convert history to format expected by RAG service
        history_for_rag = [
            {"question": h.question, "response": h.response} 
            for h in session["history"]
        ]

        # --- AGENT LOGIC ---
        # The router decides the mode ONLY IF a document is in the session context.
        # Otherwise, the mode remains 'GENERAL_QA'.
        if session.get("document_context"):
            logger.info("--- ChatEndpoint: Document found in session. Calling router. ---")
            determined_mode = service.determine_conversational_mode(
                query = message.message,
                history = history_for_rag
            )
            session["mode"] = determined_mode # Update the session state
        
        logger.info(f"--- ChatEndpoint: Current mode for session {session_id} is: {session['mode']} ---")

        # Execute the appropriate RAG method based on the current mode and context type
        if session["mode"] == "DOCUMENT_QA" and session.get("document_context"):
            doc_context = session["document_context"]
            
            # Check if we are in a simple document chat (with full_text)
            if "full_text" in doc_context:
                logger.info("--- ChatEndpoint: Executing follow-up query against simple document text. ---")
                result = service.query_simple_document(
                    question=message.message,
                    full_text=doc_context["full_text"],
                    chat_history=history_for_rag
                )
            # Otherwise, use the original, chunk-based method for complex documents
            else:
                logger.info("--- ChatEndpoint: Executing follow-up query against complex document context. ---")
                result = service.query_with_context(
                    question=message.message,
                    chat_history=history_for_rag,
                    document_chunks=doc_context.get("chunks", []) # Use .get for safety
                )
        else:
            logger.info("--- ChatEndpoint: Executing query against general knowledge base. ---")
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
=======
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
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
<<<<<<< HEAD
    # This endpoint can be used for debugging or retrieving session data
    try:
        session = get_session(session_id)
        logger.info(f"--- ChatEndpoint: Retrieved history for session {session_id}, {len(session)} messages ---")
        return {"session_id": session_id, "history": session}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to retrieve chat history: {str(e)} ---", exc_info=True)
=======
    try:
        history = chat_sessions.get(session_id, [])
        return {"session_id": session_id, "history": history}
    except Exception as e:
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
<<<<<<< HEAD
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
    """Handles the upload of a simple document (PDF or DOCX), extracts its full text, and answers the first question using a new, fast, two-step LLM chain.""" 
    try:
        # --- 1. Extract Full Text Directly from Memory ---
        filename = file.filename
        full_text = ""
        
        content = await file.read()
        
        if filename.lower().endswith('.pdf'):
            with fitz.open(stream=content, filetype="pdf") as doc:
                full_text = "".join(page.get_text() for page in doc)
        elif filename.lower().endswith('.docx'):
            doc = docx.Document(io.BytesIO(content))
            full_text = "\n".join([para.text for para in doc.paragraphs])
        else:
            raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")
        
        if not full_text:
            raise HTTPException(status_code=500, detail="Could not extract text from the document.")

        # --- 2. Get the First Answer ---
        # NOTE: We will create the 'query_simple_document' method in the next step.
        result = service.query_simple_document(
            question=message,
            full_text=full_text,
            chat_history=[] # History is empty for the first question
        )

        # --- 3. Update Session State ---
        session = get_session(session_id)
        # Store the full text instead of chunks
        session["document_context"] = {"filename": filename, "full_text": full_text}
        session["mode"] = "DOCUMENT_QA"
        
        # Store the first interaction in history
        session["history"].append(ChatHistory(
            question=message,
            response=result["response"],
            sources=[], # No sources for this method
            timestamp=datetime.now()
        ))
        
        logger.info(f"--- ChatEndpoint: Handled initial query for simple document: {filename} ---")

        return DocumentProcessingResponse(
            response=result["response"],
            document_filename=filename,
            processing_status="completed",
            sources=[],
            language=result.get("language", "es"),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"--- ChatEndpoint: Simple document chat failed: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {e}")
=======
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        return {"message": "Chat history cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
