<<<<<<< HEAD
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
=======
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
from typing import List
from datetime import datetime
import os
from pathlib import Path
from app.models.documents import DocumentUpload
from app.services.rag_service import RAGService
from app.core.config import DATA_DIR
from app.core.dependencies import get_rag_service
<<<<<<< HEAD
from app.core.auth import get_current_admin
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
import logging

router = APIRouter()
logger = logging.getLogger(__name__) 

# Ensure raw data directory exists
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(exist_ok=True)

@router.post("/documents/upload", response_model=DocumentUpload)
<<<<<<< HEAD
async def upload_document(file: UploadFile = File(...), service: RAGService = Depends(get_rag_service), admin: str = Depends(get_current_admin)):
=======
async def upload_document(file: UploadFile = File(...), service: RAGService = Depends(get_rag_service)):
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    logger.info(f"--- ENTERING API: /documents/upload for file: {file.filename if file else 'No file object'} ---")

    if not service: # Explicitly check if service is None
        logger.error("--- API: RAGService dependency injection failed, service is None. ---")
        # This should ideally be caught by Depends if get_rag_service raises HTTPException
        # but good to have an explicit check if something unexpected happens.
        raise HTTPException(status_code=500, detail="Internal server error: RAG service not available.")

    logger.info(f"--- API: RAGService successfully injected. Type: {type(service)} ---")

    try:
        logger.info(f"--- API: Inside try block for file: {file.filename} ---")
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"--- API: Invalid file type: {file.filename} ---")
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        logger.info(f"--- API: File type validated for: {file.filename} ---")

        # Save uploaded file
        file_path = RAW_DATA_DIR / file.filename

        logger.info(f"--- API: Saving uploaded file to: {file_path} ---")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"--- API: File saved successfully: {file_path} ---")

        # Process document with RAG service
        logger.info(f"--- API: Attempting to call service.process_document for: {file_path} ---")
        success = service.process_document(str(file_path))
        logger.info(f"--- API: service.process_document returned: {success} ---")
        
        if success:
            logger.info(f"--- API: Document processing successful for: {file.filename} ---")

            return DocumentUpload(
                filename=file.filename,
                status="processed",
                message="Document successfully processed and indexed",
                timestamp=datetime.now()
            )
        else:
            logger.warning(f"--- API: Document processing failed (returned False) for: {file.filename} ---")

            return DocumentUpload(
                filename=file.filename,
                status="failed",
                message="Document processing failed",
                timestamp=datetime.now()
            )
            
    except HTTPException:
        logger.error(f"--- API: HTTPException caught in /documents/upload ---", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"--- API: General Exception in /documents/upload for {file.filename if file else 'unknown_file'}: {str(e)} ---", exc_info=True)
        return DocumentUpload(
            filename=file.filename if file and hasattr(file, 'filename') else "unknown_file_error",
            status="error",
            message=f"Upload failed due to an unexpected server error: {str(e)}",
            timestamp=datetime.now()
        )

@router.get("/documents/list")
async def list_documents():
    try:
        files = []
        if RAW_DATA_DIR.exists():
            for file_path in RAW_DATA_DIR.glob("*.pdf"):
                files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime)
                })
        return {"documents": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/documents/{filename}")
<<<<<<< HEAD
async def delete_document(filename: str, admin: str = Depends(get_current_admin)):
=======
async def delete_document(filename: str):
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    try:
        file_path = RAW_DATA_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not file_path.name.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_path.unlink()
        
        return {
            "message": "Document deleted successfully",
            "filename": filename,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/documents/status")
<<<<<<< HEAD
async def get_vectorstore_status(service: RAGService = Depends(get_rag_service), admin: str = Depends(get_current_admin)):
=======
async def get_vectorstore_status(service: RAGService = Depends(get_rag_service)):
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    try:
        count = service.vector_store.get_collection_count()
        
        return {
            "total_chunks": count,
            "status": "ready" if count > 0 else "empty",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")