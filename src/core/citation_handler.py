import re
from typing import List, Dict

class CitationHandler:
    def __init__(self):
        pass

    def extract_images_from_chunks(self, chunks: List[Dict]) -> List[str]:
        """Extract all unique image paths associated with the retrieved chunks."""
        images = set()
        for chunk in chunks:
            for img in chunk.get("images", []):
                if img:
                    images.add(img)
        return list(images)
        
    def format_final_output(self, answer: str, chunks: List[Dict]) -> str:
        """Format the final output strictly according to requirements."""
        sources = set()
        for chunk in chunks:
            sources.add(f"{chunk['book']}, Page {chunk['page']}")
            
        images = self.extract_images_from_chunks(chunks)
        
        output = f"ANSWER:\n{answer}\n\n"
        output += "SOURCES:\n"
        for source in sorted(sources):
            output += f"* {source}\n"
            
        if images:
            output += "\nIMAGES:\n"
            for img in sorted(images):
                output += f"* {img}\n"
                
        return output
