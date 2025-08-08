# Path: app/core/config.py

from pathlib import Path
from dotenv import load_dotenv
import os
import secrets
import hashlib

load_dotenv()

# --- Project Paths ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# --- FastAPI Settings ---
API_TITLE = "Immigration Chatbot"
API_VERSION = "1.0.0"
DESRIPTION = "Chatbot for immigration law queries/Chatbot para consultar leyes migratorias"
HOST = "0.0.0.0"
PORT = 8000

# --- Model Settings ---
OLLAMA_MODEL = "llama3"
EMBEDDING_MODEL = "/root/local_models/paraphrase-multilingual-mpnet-base-v2"

# --- ChromaDB Settings ---
CHROMA_PERSIST_DIR = str(VECTORSTORE_DIR)
COLLECTION_NAME = "documents"

# --- Chunking Settings ---
MIN_SECTION_TEXT_LENGTH = 50
DEFAULT_HEADER_TEXT = "General Content"
CHUNK_SIZE = 750
CHUNK_OVERLAP = 75

# --- Document AI Layout Types ---
DOCUMENT_AI_HEADER_TYPES = {"heading-1", "heading-2", "heading-3", "heading-4", "heading-5", "heading-6"}
DOCUMENT_AI_PARAGRAPH_TYPES = {"paragraph"}
DOCUMENT_AI_LIST_ITEM_TYPES = {"list_item"}
DOCUMENT_AI_FOOTER_TYPES = {"footer"}
DOCUMENT_AI_TABLE_TYPES = {"table"}

# --- Google Document AI Settings ---
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us")
# Using the more specific variable name for the parser
GOOGLE_PROCESSOR_ID = os.getenv("GOOGLE_PARSER_PROCESSOR_ID", "")

# --- Chat & RAG Settings ---
MAX_MESSAGES_PER_SESSION = 10
CONTEXT_HISTORY_MESSAGES = 6 
MAX_CHUNKS_RETRIEVED = 3
LARGE_DOCUMENT_THRESHOLD = 12000

# --- Database Settings ---
DATABASE_URL = str(DATA_DIR / "users.db")

# --- Admin Authentication ---
# For session validation and password hashing
SECRET_KEY = secrets.token_urlsafe(32)

# For JWT token generation
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-that-is-long-and-random")
TOKEN_EXPIRE_HOURS = 8

# --- Ensure Directories Exist ---
DATA_DIR.mkdir(exist_ok=True)
VECTORSTORE_DIR.mkdir(exist_ok=True)