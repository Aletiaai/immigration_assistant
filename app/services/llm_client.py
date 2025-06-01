import ollama
from app.core.config import OLLAMA_MODEL

class OllamaClient:
    def __init__(self):
        self.model = OLLAMA_MODEL
        self.client = ollama.Client()  # Uses default localhost:11434
    
    def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except:
            return False