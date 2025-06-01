from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from app.core.config import EMBEDDING_MODEL

class EmbeddingService:
    def __init__(self):
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            raise Exception(f"Failed to load embedding model: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    def generate_single_embedding(self, text: str) -> List[float]:
        try:
            embedding = self.model.encode([text], convert_to_tensor=False)
            return embedding[0].tolist()
        except Exception as e:
            raise Exception(f"Single embedding generation failed: {str(e)}")