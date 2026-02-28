import fitz
from pathlib import Path
from src.core.config import IMAGES_DIR
import logging

logger = logging.getLogger(__name__)

class ImageExtractor:
    def __init__(self):
        pass

    def extract_images(self, doc: fitz.Document, book_name: str, page_num: int) -> list[dict]:
        """Extracts images from a specific page and saves them to disk."""
        image_refs = []
        try:
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            if not image_list:
                return image_refs
            
            book_images_dir = IMAGES_DIR / book_name
            book_images_dir.mkdir(parents=True, exist_ok=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                image_filename = f"page{page_num+1}_img{img_index+1}.{image_ext}"
                image_path = book_images_dir / image_filename
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                rel_path = f"data/processed/images/{book_name}/{image_filename}"
                
                image_refs.append({
                    "image_path": rel_path,
                    "book": book_name,
                    "page": page_num + 1,
                    "position": img_index + 1
                })
        except Exception as e:
             logger.error(f"Error extracting images from {book_name} page {page_num+1}: {e}")
             
        return image_refs
