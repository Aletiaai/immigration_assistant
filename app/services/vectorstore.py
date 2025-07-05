# Path: app/services/vectorstore.py

import chromadb
from typing import List, Dict
from app.core.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, DEFAULT_HEADER_TEXT
import re
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Manages all interactions with the ChromaDB vector store, including adding
    documents with rich metadata and performing similarity searches.
    """
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"} # Using cosine distance for semantic similarity
            )
            logger.info(f"--- VectorStoreService: Initialized ChromaDB client and collection '{COLLECTION_NAME}'. ---")
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to initialize ChromaDB: {e} ---", exc_info=True)
            raise

    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]) -> bool:
        """Adds a list of chunks and their embeddings to the vector store."""
        try:
            # Create a unique and descriptive ID for each chunk
            ids = [
                f"{chunk.get('document_name', 'doc')}_p{chunk.get('page', 0)}_{i}"
                for i, chunk in enumerate(chunks)
            ]
            
            documents = [chunk["content"] for chunk in chunks]
            
            metadatas = [{
                "page": str(chunk.get("page", "N/A")),
                "source": chunk.get("source", "Unknown"),
                "header": chunk.get("header", DEFAULT_HEADER_TEXT),
                "questions": "|".join(chunk.get("questions", [])),
                "original_content": chunk.get("original_content", chunk["content"])
            } for chunk in chunks]
            
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"--- VectorStoreService: Added {len(chunks)} documents to collection '{COLLECTION_NAME}'. ---")
            return True
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to add documents: {e} ---", exc_info=True)
            raise

    def search(self, query_embedding: List[float], n_results: int = 3) -> List[Dict]:
        """Performs a similarity search in the vector store."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc_content in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else float('inf')
                    
                    # Add original_content to the metadata if it's not already there
                    if 'original_content' not in metadata:
                        metadata['original_content'] = doc_content

                    search_results.append({
                        "content": doc_content,
                        "metadata": metadata,
                        "distance": distance
                    })

            logger.debug(f"--- VectorStoreService: Search returned {len(search_results)} results. ---")
            return search_results
        except Exception as e:
            logger.error(f"--- VectorStoreService: Vector search failed: {e} ---", exc_info=True)
            raise

    def get_collection_count(self) -> int:
        """Returns the total number of items in the collection."""
        try:
            count = self.collection.count()
            logger.info(f"--- VectorStoreService: Collection '{COLLECTION_NAME}' has {count} items. ---")
            return count
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to get collection count: {e} ---", exc_info=True)
            raise

    def delete_collection(self):
        """Deletes the entire collection. USE WITH CAUTION."""
        try:
            self.client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"--- VectorStoreService: Collection '{COLLECTION_NAME}' deleted. ---")
            # Recreate the collection so the service can continue to be used without restarting
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to delete collection: {e} ---", exc_info=True)
            raise