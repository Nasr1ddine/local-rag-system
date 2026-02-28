import urllib.request
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import List, Optional

from src.core.config import RAW_PDF_DIR, METADATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REGISTRY_FILE = METADATA_DIR / "pdf_registry.json"

class PDFDownloader:
    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        if REGISTRY_FILE.exists():
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=4)

    def _compute_checksum(self, filepath: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _is_valid_pdf(self, filepath: Path) -> bool:
        try:
            with open(filepath, "rb") as f:
                header = f.read(4)
                return header == b"%PDF"
        except Exception:
            return False

    def ingest_local_directory(self, source_dir: Path) -> int:
        """Scan a given directory and copy/move valid PDFs to RAW_PDF_DIR, preventing duplicates."""
        count = 0
        if not source_dir.exists() or not source_dir.is_dir():
            logger.error(f"Directory not found: {source_dir}")
            return count

        for file in source_dir.glob("*.pdf"):
            if file.is_file():
                if self.add_file(file):
                    count += 1
        return count

    def add_file(self, filepath: Path, original_url: str = None) -> bool:
        """Add a single file to the system, checking for duplicates and valid PDF type."""
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return False

        if not self._is_valid_pdf(filepath):
            logger.warning(f"Invalid PDF: {filepath}")
            return False

        checksum = self._compute_checksum(filepath)
        
        if checksum in self.registry:
            logger.info(f"Duplicate file skipped: {filepath.name} (Checksum exists)")
            return False

        dest_path = RAW_PDF_DIR / filepath.name
        
        if filepath.resolve() != dest_path.resolve():
             counter = 1
             while dest_path.exists():
                 dest_path = RAW_PDF_DIR / f"{filepath.stem}_{counter}{filepath.suffix}"
                 counter += 1
             
             shutil.copy2(filepath, dest_path)
             logger.info(f"Copied {filepath.name} to {dest_path.name}")
        else:
            logger.info(f"File already in RAW_PDF_DIR: {filepath.name}")

        self.registry[checksum] = {
            "filename": dest_path.name,
            "original_path_or_url": original_url or str(filepath),
            "size_bytes": dest_path.stat().st_size
        }
        self._save_registry()
        return True

    def download_from_urls(self, urls: List[str]) -> int:
        """Download PDFs from a list of URLs."""
        import tempfile
        count = 0
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            for idx, url in enumerate(urls):
                try:
                    logger.info(f"Downloading {url} ...")
                    filename = url.split("/")[-1]
                    if not filename.lower().endswith(".pdf"):
                        filename = f"downloaded_{idx}.pdf"
                    
                    temp_file = temp_dir_path / filename
                    urllib.request.urlretrieve(url, temp_file)
                    
                    if self.add_file(temp_file, original_url=url):
                        count += 1
                except Exception as e:
                    logger.error(f"Failed to download {url}: {e}")
        return count
