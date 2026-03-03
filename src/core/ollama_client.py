import logging
import ollama

from src.core.config import LLM_MODEL, OLLAMA_HOST

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model_name=LLM_MODEL):
        self.model_name = model_name
        self._client = ollama.Client(host=OLLAMA_HOST)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send chat request to Ollama."""
        try:
            response = self._client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error during Ollama generation: {e}")
            return "Error: Could not generate a response from the model."
