#main.py

import sys
import uvicorn
import subprocess
import logging
from pathlib import Path

# --- Setup Project Path ---
# This ensures that the 'app' module can be found
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Configure Logging ---
# A single logging configuration for the entire application startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Main Application ---
def main():
    """
    Main entry point for starting the RAG chat system.
    Handles dynamic host detection and robust error handling.
    """
    try:
        # Import configuration after path setup
        from app.core.config import HOST, PORT, API_TITLE
        from app.main import app
    except ImportError as e:
        logger.critical(f"Failed to import application modules: {e}")
        logger.critical("Please ensure all dependencies are installed from requirements.txt")
        sys.exit(1)

    # --- Host Detection ---
    # Try to get the Tailscale IP, but fall back gracefully
    run_host = HOST
    try:
        tailscale_ip = subprocess.check_output(['tailscale', 'ip', '-4'], text=True).strip()
        if tailscale_ip:
            run_host = tailscale_ip
            logger.info(f"Tailscale IP detected. Using {run_host} as host.")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.warning(f"Tailscale command not found or failed: {e}. Falling back to default host: {HOST}")
        run_host = HOST

    # --- Server Startup ---
    try:
        logger.info(f"Starting {API_TITLE} server...")
        logger.info(f"Access the application at: http://{run_host}:{PORT}")
        logger.info("Press Ctrl+C to stop the server.")

        uvicorn.run(
            "app.main:app",
            host=run_host,
            port=PORT,
            reload=True,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.critical(f"Failed to start Uvicorn server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()