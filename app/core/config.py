from pathlib import Path
from dotenv import load_dotenv
import os
<<<<<<< HEAD
import secrets
import hashlib
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# FastAPI settings
API_TITLE = "Immigration Chatbot"
API_VERSION = "1.0.0"
DESRIPTION = "Chatbot for immigration law queries/Chatbot para consultar leyes migratorias"
HOST = "0.0.0.0"
PORT = 8000

# Model settings
OLLAMA_MODEL = "llama3"
EMBEDDING_MODEL = "/root/local_models/paraphrase-multilingual-mpnet-base-v2"

# ChromaDB settings
CHROMA_PERSIST_DIR = str(VECTORSTORE_DIR)
COLLECTION_NAME = "documents"

# Chunking settings
MIN_SECTION_TEXT_LENGTH = 50  # Minimum characters for a text block to be considered substantial content
DEFAULT_HEADER_TEXT = "General Content"
CHUNK_SIZE = 750  # Target character size for final chunks
CHUNK_OVERLAP = 75 # Character overlap between chunks

# Header types from Document AI Layout Parser (from your JSON example)
DOCUMENT_AI_HEADER_TYPES = {"heading-1", "heading-2", "heading-3", "heading-4", "heading-5", "heading-6"} # Add more if they appear
DOCUMENT_AI_PARAGRAPH_TYPES = {"paragraph"} # "text" might also appear in some processors
DOCUMENT_AI_LIST_ITEM_TYPES = {"list_item"} # Add if your docs have lists
DOCUMENT_AI_FOOTER_TYPES = {"footer"} # To potentially ignore footers
DOCUMENT_AI_TABLE_TYPES = {"table"}   # To handle tables specifically

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
VECTORSTORE_DIR.mkdir(exist_ok=True)

# Google Document AI settings (for online document processing)
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us")  # or "eu"
<<<<<<< HEAD
GOOGLE_PROCESSOR_ID = os.getenv("GOOGLE_PARSER_PROCESSOR_ID", "") #GOOGLE_PROCESSOR_ID   GOOGLE_PARSER_PROCESSOR_ID

# Chat settings
MAX_MESSAGES_PER_SESSION = 10
CONTEXT_HISTORY_MESSAGES = 6

# Chunk settings
MAX_CHUNKS_RETRIEVED = 3

# auth configuration 
SECRET_KEY = secrets.token_urlsafe(32)  # Generate secure key
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()
TOKEN_EXPIRE_HOURS = 8

# Admin Authentication
ADMIN_PASSWORD = "your_secure_password_here"
JWT_SECRET_KEY = "your-secret-key-here"
JWT_EXPIRE_HOURS = 8
=======
GOOGLE_PROCESSOR_ID = os.getenv("GOOGLE_PROCESSOR_ID", "") #GOOGLE_PROCESSOR_ID   GOOGLE_PARSER_PROCESSOR_ID

# Chat settings
MAX_MESSAGES_PER_SESSION = 10
CONTEXT_HISTORY_MESSAGES = 5

# Chunk settings
MAX_CHUNKS_RETRIEVED = 3
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
