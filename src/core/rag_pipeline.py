import logging
from typing import List, Dict

from src.core.retriever import Retriever
from src.core.prompt_builder import PromptBuilder
from src.core.ollama_client import OllamaClient
from src.core.citation_handler import CitationHandler

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.prompt_builder = PromptBuilder()
        self.llm_client = OllamaClient()
        self.citation_handler = CitationHandler()

    def query(self, user_question: str) -> str:
        """Full pipeline: retrieve -> prompt -> generate -> format formatting."""
        logger.info(f"Processing query: '{user_question}'")
        
        # 1. Retrieve
        retrieved_chunks = self.retriever.retrieve(user_question)
        if not retrieved_chunks:
            return "No relevant context found to answer the query."
            
        # 2. Build Prompt
        system_prompt = self.prompt_builder.system_prompt
        user_prompt = self.prompt_builder.build_prompt(user_question, retrieved_chunks)
        
        # 3. Generate
        answer = self.llm_client.generate(system_prompt, user_prompt)
        
        # 4. Format Output with Citations
        final_output = self.citation_handler.format_final_output(answer, retrieved_chunks)
        
        return final_output
