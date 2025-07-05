<<<<<<< HEAD
<<<<<<< HEAD
from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
=======
from fastapi import FastAPI, HTTPException
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
>>>>>>> 8b2611b (Admin login page created and integrated with the uploading documents process)
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn
import logging
<<<<<<< HEAD
<<<<<<< HEAD
from datetime import datetime
from app.api import chat, documents
from app.core.config import API_TITLE, API_VERSION, DESRIPTION, HOST, PORT
from app.api import chat, documents, auth 

router = APIRouter()
=======
from app.api import chat, documents
from app.core.config import API_TITLE, API_VERSION, DESRIPTION, HOST, PORT
from app.api import chat, documents
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
from datetime import datetime
from app.api import chat, documents
from app.core.config import API_TITLE, API_VERSION, DESRIPTION, HOST, PORT
from app.api import chat, documents, auth 

router = APIRouter()
>>>>>>> 8b2611b (Admin login page created and integrated with the uploading documents process)

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to logging.INFO for less verbose output during development
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Outputs to console
        # I can add logging.FileHandler("app.log") here to log to a file
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title = API_TITLE,
    version = API_VERSION,
    description = DESRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
<<<<<<< HEAD
<<<<<<< HEAD
app.include_router(auth.router, prefix="/api", tags=["auth"])

=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
app.include_router(auth.router, prefix="/api", tags=["auth"])

>>>>>>> 8b2611b (Admin login page created and integrated with the uploading documents process)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface"""
    try:
        html_file = Path(__file__).parent / "static" / "index.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(), status_code=200)
        else:
            return HTMLResponse(
                content="<h1>RAG Chat System</h1><p>Frontend files not found. Please add static files.</p>",
                status_code=200
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve frontend: {str(e)}")
    
@app.get("/documents", response_class=HTMLResponse)
async def documents_page():
    """Serve the document management interface"""
    try:
        html_file = Path(__file__).parent / "static" / "documents.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(), status_code=200)
        else:
            return HTMLResponse(
                content="<h1>Document Management</h1><p>Frontend file not found.</p>",
                status_code=404
            )
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error serving documents.html: {e}") # Or use proper logging
        raise HTTPException(status_code=500, detail=f"Failed to serve document management page: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "RAG Chat System",
            "version": API_VERSION
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8b2611b (Admin login page created and integrated with the uploading documents process)
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the admin login page"""
    try:
        html_file = Path(__file__).parent / "static" / "login.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(), status_code=200)
        else:
            return HTMLResponse(
                content="<h1>Login Page</h1><p>Login page not found.</p>",
                status_code=404
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve login page: {str(e)}")

<<<<<<< HEAD
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
>>>>>>> 8b2611b (Admin login page created and integrated with the uploading documents process)
if __name__ == "__main__":
    try:
        uvicorn.run(
            "app.main:app",
            host=HOST,
            port=PORT,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"Failed to start server: {str(e)}")