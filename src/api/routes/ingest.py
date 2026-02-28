import logging
import asyncio
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from src.models.schemas import IngestUrlRequest, IngestResponse, GenericResponse
from src.ingestion.downloader import PDFDownloader
from src.ingestion.parser import PDFParser
from src.ingestion.chunker import TextChunker
from src.storage.chroma_store import VectorStore
from src.core.config import RAW_PDF_DIR
import shutil

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingestion"])

def process_pdf(file_path_or_url: str):
    """Background task to run the full ingestion pipeline on a single source"""
    logger.info(f"Starting background ingestion for {file_path_or_url}")
    try:
        downloader = PDFDownloader()
        
        # Download logic
        if file_path_or_url.startswith("http"):
            downloader.download_from_urls([file_path_or_url])
        else:
            downloader.ingest_local_directory(RAW_PDF_DIR)
            
        logger.info("Starting PDF parsing...")
        parser = PDFParser()
        parser.parse_all_pdfs()
        
        logger.info("Starting text chunking...")
        chunker = TextChunker()
        chunks = chunker.chunk_all_parsed_files()
        
        if chunks:
            logger.info(f"Adding {len(chunks)} chunks to Vector Store...")
            vector_store = VectorStore()
            vector_store.add_chunks(chunks)
            logger.info("Ingestion complete.")
        else:
            logger.warning("No chunks generated.")
    except Exception as e:
        logger.error(f"Error during ingestion pipeline: {str(e)}")


@router.post("/file", response_model=IngestResponse)
async def ingest_file(bg: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    file_path = RAW_PDF_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Dispatch background ingestion task
    bg.add_task(process_pdf, str(file_path))
    
    return IngestResponse(
        status="success",
        book=file.filename,
        chunks_added=0 # will be processed async
    )

@router.post("/url", response_model=IngestResponse)
async def ingest_url(bg: BackgroundTasks, request: IngestUrlRequest):
    url_str = str(request.url)
    
    # Dispatch background ingestion task
    bg.add_task(process_pdf, url_str)
    
    return IngestResponse(
        status="success",
        book=url_str,
        chunks_added=0 # will be processed async
    )
