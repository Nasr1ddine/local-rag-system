import logging
from typing import List, Dict

from src.storage.chroma_store import VectorStore
from src.core.config import TOP_K_RETRIEVAL

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Dict]:
        """Retrieve most relevant chunks for a given query."""
        logger.info(f"Retrieving top {top_k} chunks for query: '{query}'")
        results = self.vector_store.query(query, n_results=top_k)
        
        retrieved_chunks = []
        if not results["documents"] or not results["documents"][0]:
            return retrieved_chunks
            
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else []
        
        for i in range(len(docs)):
            metadata = metas[i]
            images_str = metadata.get("image_refs", "")
            images = images_str.split(",") if images_str else []
            
            chunk = {
                "text": docs[i],
                "book": metadata.get("book", "Unknown"),
                "page": metadata.get("page", 0),
                "images": images,
                "distance": distances[i] if i < len(distances) else None
            }
            retrieved_chunks.append(chunk)
            
        return retrieved_chunks
