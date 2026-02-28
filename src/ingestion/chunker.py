import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.config import TEXT_DIR, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class TextChunker:
    def __init__(self, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        # Approximate 1 token = 4 characters for recursive splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 4,
            chunk_overlap=self.overlap * 4,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_all_parsed_files(self) -> List[Dict]:
        """Reads all parsed JSON files and chunks them."""
        all_chunks = []
        for file in TEXT_DIR.glob("*_parsed.json"):
            logger.info(f"Chunking {file.name}...")
            chunks = self.chunk_file(file)
            all_chunks.extend(chunks)
        return all_chunks

    def chunk_file(self, parsed_file: Path) -> List[Dict]:
        """Chunks a single parsed JSON file."""
        chunks = []
        with open(parsed_file, "r", encoding="utf-8") as f:
            pages = json.load(f)
            
        for page in pages:
            book_title = page["book_title"]
            page_number = page["page_number"]
            text = page.get("text", "")
            images = page.get("images", [])
            
            if not text.strip():
                continue
                
            text_chunks = self.splitter.split_text(text)
            
            for idx, text_chunk in enumerate(text_chunks):
                chunk_id = self._generate_chunk_id(book_title, page_number, idx, text_chunk)
                
                chunk_data = {
                    "chunk_id": chunk_id,
                    "text": text_chunk,
                    "book": book_title,
                    "page": page_number,
                    "source_file": parsed_file.name,
                    "image_refs": images
                }
                chunks.append(chunk_data)
                
        return chunks

    def _generate_chunk_id(self, book_title: str, page_number: int, index: int, text: str) -> str:
        """Generate a unique deterministic ID for a chunk."""
        content = f"{book_title}_{page_number}_{index}_{text[:50]}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()
