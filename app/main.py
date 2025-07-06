# Path: app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn
import logging
import subprocess
from app.api import chat, documents, auth
from app.core.config import API_TITLE, API_VERSION, DESRIPTION, HOST, PORT

# Configure basic logging to see application events in the console
logging.basicConfig(
    level=logging.INFO, # Use INFO for production, DEBUG for development
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

# Configure CORS (Cross-Origin Resource Sharing) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routers from other modules
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Mount the 'static' directory to serve frontend files
static_path = Path(__file__).parent / "static"
if static_path.exists() and static_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# --- HTML Page Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_chat_page():
    """Serves the main chat interface (index.html)."""
    html_file = static_path / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/documents", response_class=HTMLResponse)
async def serve_documents_page():
    """Serves the document management interface (documents.html)."""
    html_file = static_path / "documents.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    raise HTTPException(status_code=404, detail="documents.html not found")

@app.get("/login", response_class=HTMLResponse)
async def serve_login_page():
    """Serves the admin login page (login.html)."""
    html_file = static_path / "login.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    raise HTTPException(status_code=404, detail="login.html not found")

# --- Health Check Endpoint ---

@app.get("/health")
async def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "healthy", "service": API_TITLE, "version": API_VERSION}

# --- Server Startup ---

if __name__ == "__main__":
    try:
        tailscale_ip = subprocess.check_output(['tailscale', 'ip', '-4']).decode().strip()
        logger.info(f"Starting server at http://{tailscale_ip}:{PORT}")
        uvicorn.run(
            "app.main:app",
            host=tailscale_ip,
            port=PORT,
            reload=True, # Enables auto-reload for development
            log_level="info"
        )
    except Exception as e: # Catch all exceptions here
        if "tailscale" in str(e).lower() or "no such file or directory" in str(e).lower():
            logger.info("Tailscale command failed or not found. Falling back to default host.")
            logger.info(f"Starting server at http://{HOST}:{PORT}")
            uvicorn.run(
                "app.main:app",
                host=HOST,
                port=PORT,
                reload=True, # Enables auto-reload for development
                log_level="info"
            )
        else:
            logger.critical(f"Failed to start server: {e}", exc_info=True)