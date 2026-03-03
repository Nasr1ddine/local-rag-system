import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEXT_DIR = PROCESSED_DATA_DIR / "text"
IMAGES_DIR = PROCESSED_DATA_DIR / "images"
METADATA_DIR = PROCESSED_DATA_DIR / "metadata"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
MODELS_DIR = BASE_DIR / "models"

# ── Ollama ────────────────────────────────────────────────────────────────────
# Override via OLLAMA_HOST env var (e.g. http://ollama:11434 in Docker)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ── Model Configuration ───────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# ── Chunking Configuration ────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# ── Retrieval Configuration ───────────────────────────────────────────────────
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        RAW_PDF_DIR,
        TEXT_DIR,
        IMAGES_DIR,
        METADATA_DIR,
        VECTOR_STORE_DIR,
        MODELS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
