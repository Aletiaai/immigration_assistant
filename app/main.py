#app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging
from app.api import chat, documents, auth
from app.core.config import API_TITLE, API_VERSION, DESRIPTION

# Configure basic logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize the FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=DESRIPTION
)

# Add middleware for Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be more specific for production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API endpoint routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# --- Static File and HTML Page Serving with Error Handling ---

static_path = Path(__file__).parent / "static"

# This must come *after* the API routes to avoid conflicts.
if static_path.exists() and static_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    logger.error(f"Static directory not found at {static_path}. Frontend will not be served.")

@app.get("/", response_class=HTMLResponse)
async def serve_chat_page():
    """Serves the main chat interface (index.html) with robust error handling."""
    html_file = static_path / "index.html"
    try:
        if not html_file.is_file():
            logger.error("Frontend file not found: index.html")
            raise HTTPException(status_code=404, detail="Frontend file 'index.html' not found.")
        return HTMLResponse(content=html_file.read_text())
    except Exception as e:
        logger.critical(f"Failed to read and serve index.html: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load the main application page.")

@app.get("/documents", response_class=HTMLResponse)
async def serve_documents_page():
    """Serves the document management page (documents.html) with robust error handling."""
    html_file = static_path / "documents.html"
    try:
        if not html_file.is_file():
            logger.error("Frontend file not found: documents.html")
            raise HTTPException(status_code=404, detail="Frontend file 'documents.html' not found.")
        return HTMLResponse(content=html_file.read_text())
    except Exception as e:
        logger.critical(f"Failed to read and serve documents.html: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load the document management page.")

@app.get("/login", response_class=HTMLResponse)
async def serve_login_page():
    """Serves the admin login page (login.html) with robust error handling."""
    html_file = static_path / "login.html"
    try:
        if not html_file.is_file():
            logger.error("Frontend file not found: login.html")
            raise HTTPException(status_code=404, detail="Frontend file 'login.html' not found.")
        return HTMLResponse(content=html_file.read_text())
    except Exception as e:
        logger.critical(f"Failed to read and serve login.html: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load the login page.")

@app.get("/health")
async def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "healthy", "service": API_TITLE, "version": API_VERSION}