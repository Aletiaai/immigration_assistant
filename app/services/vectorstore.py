import chromadb
from typing import List, Dict, Optional
from app.core.config import CHROMA_PERSIST_DIR, COLLECTION_NAME

class VectorStoreService:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise Exception(f"Failed to initialize ChromaDB: {str(e)}")
    
    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]) -> bool:
        try:
            ids = [f"doc_{i}" for i in range(len(chunks))]
            documents = [chunk["content"] for chunk in chunks]
            metadatas = [{
                "page": chunk.get("page", 1),
                "type": chunk.get("type", "block"),
                "source": chunk.get("source", "unknown")
            } for chunk in chunks]
            
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to add documents: {str(e)}")
    
    def search(self, query_embedding: List[float], n_results: int = 3) -> List[Dict]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    search_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return search_results
        except Exception as e:
            raise Exception(f"Vector search failed: {str(e)}")
    
    def get_collection_count(self) -> int:
        try:
            return self.collection.count()
        except Exception as e:
            raise Exception(f"Failed to get collection count: {str(e)}")