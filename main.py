import typer
import logging
from pathlib import Path

from src.core.config import ensure_directories, RAW_PDF_DIR
from src.ingestion.downloader import PDFDownloader
from src.ingestion.parser import PDFParser
from src.ingestion.chunker import TextChunker
from src.storage.chroma_store import VectorStore
from src.core.rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer(help="Local RAG System CLI")

@app.command()
def ingest(source: str = None):
    """Ingest PDFs from a directory or URLs. If no source given, tries to ingest from data/raw_pdfs."""
    ensure_directories()
    
    downloader = PDFDownloader()
    if source:
        source_path = Path(source)
        if source_path.exists() and source_path.is_dir():
            logger.info(f"Ingesting directory: {source_path}")
            added = downloader.ingest_local_directory(source_path)
            logger.info(f"Added {added} new PDFs from directory.")
        elif source.startswith("http"):
            logger.info(f"Downloading from URL: {source}")
            added = downloader.download_from_urls([source])
            logger.info(f"Downloaded {added} new PDFs.")
        else:
            logger.error(f"Invalid source: {source}. Provide a directory path or URL.")
            return
            
    # Parse all PDFs
    logger.info("Starting PDF parsing...")
    parser = PDFParser()
    parser.parse_all_pdfs()
    logger.info("PDF parsing complete.")

@app.command()
def embed():
    """Chunk parsed text and generate embeddings, storing them in ChromaDB."""
    ensure_directories()
    
    logger.info("Starting text chunking...")
    chunker = TextChunker()
    chunks = chunker.chunk_all_parsed_files()
    
    if not chunks:
        logger.warning("No chunks generated. Make sure you run 'ingest' first.")
        return
        
    logger.info(f"Generated {len(chunks)} chunks. Adding to Vector Store...")
    vector_store = VectorStore()
    vector_store.add_chunks(chunks)
    logger.info("Embedding process complete.")

@app.command()
def query(question: str):
    """Query the RAG system with a question."""
    ensure_directories()
    
    pipeline = RAGPipeline()
    print("\n" + "="*50)
    print(f"QUERY: {question}")
    print("="*50 + "\n")
    
    response = pipeline.query(question)
    print(response)

if __name__ == "__main__":
    ensure_directories()
    app()
