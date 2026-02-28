import chromadb
import logging
from typing import List, Dict

from src.core.config import VECTOR_STORE_DIR
from src.ingestion.embedder import Embedder

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        self.collection = self.client.get_or_create_collection(
            name="rag_documents"
        )
        self.embedder = Embedder()

    def add_chunks(self, chunks: List[Dict]):
        """Add document chunks to the vector store with their embeddings."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        
        existing = self.collection.get(ids=[c["chunk_id"] for c in chunks])
        existing_ids = set(existing["ids"])
        
        chunks_to_add = [c for c in chunks if c["chunk_id"] not in existing_ids]
        if not chunks_to_add:
            logger.info("All chunks already exist in vector store.")
            return

        texts_to_add = [c["text"] for c in chunks_to_add]
        logger.info(f"Generating embeddings for {len(texts_to_add)} chunks...")
        embeddings = self.embedder.generate_embeddings_batch(texts_to_add)

        ids = [c["chunk_id"] for c in chunks_to_add]
        metadatas = []
        for c in chunks_to_add:
            image_refs_str = ",".join([img.get("image_path", "") for img in c.get("image_refs", []) if isinstance(img, dict)])
            metadata = {
                "book": c["book"],
                "page": c["page"],
                "chunk_id": c["chunk_id"],
                "source_file": c["source_file"],
                "image_refs": image_refs_str
            }
            metadatas.append(metadata)

        logger.info(f"Adding {len(ids)} chunks to ChromaDB...")
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                documents=texts_to_add[i:i+batch_size]
            )

    def query(self, query_text: str, n_results: int = 5) -> dict:
        """Query the vector store for the closest chunks."""
        query_embedding = self.embedder.generate_embedding(query_text)
        if not query_embedding:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
