# Path: app/api/chat.py

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any
from datetime import datetime
from app.models.chat import ChatMessage, ChatResponse, ChatHistory, DocumentProcessingResponse
from app.services.rag_service import RAGService
from app.core.dependencies import get_rag_service
import logging
import io
import docx
import fitz # PyMuPDF

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for chat sessions
chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str) -> Dict[str, Any]:
    """
    Retrieves or creates a chat session.
    A session includes 'history', 'document_context', and a 'mode'.
    """
    if session_id not in chat_sessions:
        logger.info(f"--- Creating new session: {session_id} ---")
        chat_sessions[session_id] = {
            "history": [],
            "document_context": None,
            "mode": "GENERAL_QA"
        }
    return chat_sessions[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, service: RAGService = Depends(get_rag_service)):
    """
    Handles chat messages using a stateful, state-aware agent model.
    """
    try:
        session = get_session(message.session_id)
        history_for_rag = [{"question": h.question, "response": h.response} for h in session["history"]]
        
        # Determine if a document is loaded in the current session
        document_is_loaded = "document_context" in session and session["document_context"] is not None

        # The router now uses the document_is_loaded status to make a better decision
        determined_mode = service.determine_conversational_mode(
            query=message.message,
            history=history_for_rag,
            document_in_session=document_is_loaded
        )
        session["mode"] = determined_mode
        
        logger.info(f"--- ChatEndpoint: Mode for session {message.session_id} set to: {session['mode']} ---")

        # Execute the appropriate RAG method based on the determined mode
        if session["mode"] == "DOCUMENT_QA" and document_is_loaded:
            # This logic correctly handles both simple (full_text) and complex (chunks) documents
            doc_context = session["document_context"]
            if "full_text" in doc_context:
                result = service.query_simple_document(
                    question=message.message,
                    full_text=doc_context["full_text"],
                    chat_history=history_for_rag
                )
            else: # Fallback for complex documents, not used in your current flow but good practice
                 result = service.query_with_context(
                    question=message.message,
                    chat_history=history_for_rag,
                    document_chunks=doc_context.get("chunks", [])
                )
        else:
            # This path is taken if the router decides GENERAL_KNOWLEDGE_BASE
            logger.info("--- ChatEndpoint: Executing query against general knowledge base. ---")
            result = service.query(message.message, history_for_rag)

        # --- RESPONSE HANDLING ---
        response = ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            language=result.get("language", "en"),
            timestamp=datetime.now()
        )
        
        session["history"].append(ChatHistory(
            question=message.message,
            response=response.response,
            sources=response.sources,
            timestamp=response.timestamp
        ))
        
        return response
        
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Error processing chat: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")
    
@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Retrieves all data for a given session for debugging."""
    try:
        session = get_session(session_id)
        logger.info(f"--- ChatEndpoint: Retrieved history for session {session_id} ---")
        return {"session_id": session_id, "history": session["history"], "document_context": session.get("document_context"), "mode": session.get("mode")}
    except Exception as e:
        logger.error(f"--- ChatEndpoint: Failed to retrieve chat history: {str(e)} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clears all data for a session."""
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
    session_id: str = Form(...),  # This is the corrected line
    service: RAGService = Depends(get_rag_service)
):
    """
    Handles the upload of a simple document. It now correctly uses the session_id
    provided by the client to maintain the conversation context.
    """
    try:
        filename = file.filename
        content = await file.read()
        full_text = ""
        
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

        result = service.query_simple_document(
            question=message,
            full_text=full_text,
            chat_history=[]
        )
        
        # This now uses the correct session_id from the form
        session = get_session(session_id)
        session["document_context"] = {"filename": filename, "full_text": full_text}
        session["mode"] = "DOCUMENT_QA"
        
        session["history"].append(ChatHistory(
            question=message,
            response=result["response"],
            sources=[],
            timestamp=datetime.now()
        ))
        
        logger.info(f"--- ChatEndpoint: Handled initial query for document '{filename}' in session '{session_id}' ---")

        return DocumentProcessingResponse(
            response=result["response"],
            document_filename=filename,
            processing_status="completed",
            sources=[],
            language=result.get("language", "en"),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"--- ChatEndpoint: Simple document chat failed: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {e}")