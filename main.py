#!/usr/bin/env python3
import sys
import uvicorn
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from app.core.config import HOST, PORT, API_TITLE
    from app.main import app
except ImportError as e:
    print(f"Failed to import application modules: {str(e)}")
    print("Make sure all dependencies are installed and the project structure is correct.")
    sys.exit(1)

def main():
    """Main entry point for the RAG chat system"""
    try:
        print(f"Starting {API_TITLE}...")
        print(f"Server will be available at: http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()