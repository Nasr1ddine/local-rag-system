import fitz
import json
import logging
from pathlib import Path
from typing import List, Dict

from src.core.config import RAW_PDF_DIR, TEXT_DIR
from src.ingestion.image_extractor import ImageExtractor

logger = logging.getLogger(__name__)

class PDFParser:
    def __init__(self):
        self.image_extractor = ImageExtractor()

    def parse_all_pdfs(self) -> List[Path]:
        """Parse all PDFs in RAW_PDF_DIR and save text outputs."""
        parsed_files = []
        for pdf_file in RAW_PDF_DIR.glob("*.pdf"):
            output_file = TEXT_DIR / f"{pdf_file.stem}_parsed.json"
            if output_file.exists():
                logger.info(f"Skipping already parsed file: {pdf_file.name}")
                parsed_files.append(output_file)
                continue
            
            logger.info(f"Parsing {pdf_file.name}...")
            parsed_data = self.parse_pdf(pdf_file)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            parsed_files.append(output_file)
            
        return parsed_files

    def parse_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract text and images from a single PDF."""
        book_title = pdf_path.stem
        parsed_pages = []
        
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc() # [level, title, page]
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if not text.strip():
                    continue # Skip empty pages
                
                chapter = self._detect_chapter(toc, page_num + 1)
                image_refs = self.image_extractor.extract_images(doc, book_title, page_num)
                
                page_data = {
                    "book_title": book_title,
                    "page_number": page_num + 1,
                    "text": text.strip(),
                    "images": image_refs
                }
                if chapter:
                    page_data["chapter"] = chapter
                    
                parsed_pages.append(page_data)
                
        except Exception as e:
            logger.error(f"Failed to parse {pdf_path.name}: {e}")
            
        return parsed_pages

    def _detect_chapter(self, toc: list, current_page: int) -> str:
        """Find the most recent chapter title from TOC for the given page."""
        current_chapter = None
        for item in toc:
            level, title, page = item
            if page <= current_page:
                if level == 1:
                    current_chapter = title
            else:
                break
        return current_chapter
