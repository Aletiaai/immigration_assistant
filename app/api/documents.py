from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from datetime import datetime
from pathlib import Path
from app.models.documents import DocumentUpload
from app.services.rag_service import RAGService
from app.core.config import DATA_DIR
from app.core.dependencies import get_rag_service
from app.core.auth import get_current_admin
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure the directory for raw data exists
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(exist_ok=True)

@router.post("/documents/upload", response_model=DocumentUpload)
async def upload_document(
    file: UploadFile = File(...),
    service: RAGService = Depends(get_rag_service),
    admin: str = Depends(get_current_admin)
):
    """
    Handles the upload and processing of a document for the knowledge base.
    This endpoint is protected and requires admin authentication.
    """
    logger.info(f"--- Document Upload endpoint for file: {file.filename} ---")
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for the knowledge base.")

        file_path = RAW_DATA_DIR / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"--- File saved, starting processing: {file_path} ---")
        success = service.process_document(str(file_path))
        
        if success:
            logger.info(f"--- Document processing successful: {file.filename} ---")
            return DocumentUpload(
                filename=file.filename,
                status="processed",
                message="Document successfully processed and indexed.",
                timestamp=datetime.now()
            )
        else:
            logger.error(f"--- Document processing failed for: {file.filename} ---")
            raise HTTPException(status_code=500, detail="Document processing failed by the service.")

    except Exception as e:
        logger.error(f"--- Exception in /documents/upload: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/documents/list")
async def list_documents(admin: str = Depends(get_current_admin)):
    """Lists all documents currently in the knowledge base."""
    try:
        files = [
            {
                "filename": p.name,
                "size": p.stat().st_size,
                "created": datetime.fromtimestamp(p.stat().st_ctime)
            }
            for p in RAW_DATA_DIR.glob("*.pdf") if p.is_file()
        ]
        return {"documents": files}
    except Exception as e:
        logger.error(f"--- Failed to list documents: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents.")

@router.delete("/documents/{filename}")
async def delete_document(filename: str, admin: str = Depends(get_current_admin)):
    """Deletes a document from the knowledge base."""
    try:
        file_path = RAW_DATA_DIR / filename
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Document not found.")
        
        file_path.unlink()  # Deletes the file
        
        # You might want to add logic here to remove the document from the vector store as well
        logger.info(f"--- Document deleted: {filename} ---")
        return {"message": "Document deleted successfully", "filename": filename}
    except Exception as e:
        logger.error(f"--- Failed to delete document: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")

@router.get("/documents/status")
async def get_vectorstore_status(
    service: RAGService = Depends(get_rag_service),
    admin: str = Depends(get_current_admin)
):
    """Gets the status of the vector store in the RAG service."""
    try:
        count = service.vector_store.get_collection_count()
        return {
            "status": "ready" if count > 0 else "empty",
            "total_chunks": count,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"--- Failed to get vector store status: {e} ---", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vector store status: {e}")