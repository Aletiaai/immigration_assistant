import chromadb
from typing import List, Dict, Optional
from app.core.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, DEFAULT_HEADER_TEXT
import re
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"--- VectorStoreService: Initialized ChromaDB client and collection '{COLLECTION_NAME}'. ---")
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to initialize ChromaDB: {str(e)} ---", exc_info=True)
            raise Exception(f"Failed to initialize ChromaDB: {str(e)}")
    
    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]) -> bool:
        try:
            ids = [f"{chunk.get('document_name', 'unknown_doc')}_page{chunk.get('page',0)}_header_{re.sub(r'[^a-zA-Z0-9_-]', '', chunk.get('header', DEFAULT_HEADER_TEXT)[:30])}_{i}" for i, chunk in enumerate(chunks)]

            documents = [chunk["content"] for chunk in chunks]
            metadatas = [{
                "page": str(chunk.get("page", "N/A")), # Ensure page is string for Chroma
                "type": chunk.get("type", "block"),
                "source": chunk.get("document_name", "unknown_source"),
                "header": chunk.get("header", DEFAULT_HEADER_TEXT)
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
            logger.error(f"--- VectorStoreService: Failed to add documents: {str(e)} ---", exc_info=True)
            raise Exception(f"Failed to add documents: {str(e)}")
    
    def search(self, query_embedding: List[float], n_results: int = 3) -> List[Dict]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc_content in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0
                    search_results.append({
                        "content": doc_content,
                        "metadata": metadata,
                        "distance": distance
                    })
            logger.debug(f"--- VectorStoreService: Search returned {len(search_results)} results. ---")
            return search_results
        except Exception as e:
            logger.error(f"--- VectorStoreService: Vector search failed: {str(e)} ---", exc_info=True)
            raise Exception(f"Vector search failed: {str(e)}")
    
    def get_collection_count(self) -> int:
        try:
            count = self.collection.count()
            logger.info(f"--- VectorStoreService: Collection '{COLLECTION_NAME}' has {count} items. ---")
            return count
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to get collection count: {str(e)} ---", exc_info=True)
            raise Exception(f"Failed to get collection count: {str(e)}")
        
    def delete_collection(self):
        """Deletes the collection."""
        try:
            self.client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"--- VectorStoreService: Collection '{COLLECTION_NAME}' deleted. ---")
            # Recreate it empty if you want to continue using the service instance
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"--- VectorStoreService: Failed to delete collection: {str(e)} ---", exc_info=True)
            raise Exception(f"Failed to delete collection: {str(e)}")