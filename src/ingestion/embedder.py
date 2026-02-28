import logging
import ollama
from typing import List

from src.core.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name=EMBEDDING_MODEL):
        self.model_name = model_name

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using Ollama."""
        embeddings = []
        try:
            for text in texts:
                response = ollama.embeddings(
                    model=self.model_name,
                    prompt=text
                )
                embeddings.append(response["embedding"])
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise e
        return embeddings

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        try:
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
