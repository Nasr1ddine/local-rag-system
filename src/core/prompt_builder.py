from typing import List, Dict

class PromptBuilder:
    def __init__(self):
        self.system_prompt = (
            "You are a helpful and precise assistant answering questions using the provided book excerpts.\n"
            "Rules:\n"
            "* Only answer from provided context. Do not use outside knowledge.\n"
            "* Cite sources strictly using the format: (Book Name, Page X)\n"
            "* If you are unsure or the context does not contain the answer, say you don't know.\n"
            "* Include image references if relevant to your answer.\n"
        )

    def build_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Constructs the final prompt with context and query."""
        context_str = ""
        for chunk in retrieved_chunks:
            book = chunk["book"]
            page = chunk["page"]
            text = chunk["text"]
            images = chunk["images"]
            
            context_str += f"[Book: {book}, Page: {page}]\n"
            context_str += f"Text: {text}\n"
            for img in images:
                if img:
                    context_str += f"Image: {img}\n"
            context_str += "\n"
            
        full_prompt = (
            f"Context Information:\n{context_str}\n"
            f"User Question: {query}\n\n"
            "Answer:"
        )
        return full_prompt
