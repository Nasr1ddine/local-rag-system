import logging
from typing import List
from fastapi import APIRouter, HTTPException
from src.core.config import RAW_PDF_DIR
from src.models.schemas import BookListResponse, GenericResponse
from src.storage.chroma_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/books", tags=["Books"])

@router.get("", response_model=BookListResponse)
async def list_books():
    books = [f.name for f in RAW_PDF_DIR.glob("*.pdf")]
    return BookListResponse(books=books)

@router.delete("/{book_name}", response_model=GenericResponse)
async def delete_book(book_name: str):
    logger.info(f"Requests deletion for {book_name}")
    pdf_path = RAW_PDF_DIR / book_name
    if pdf_path.exists():
        pdf_path.unlink()
        # TODO: Implement deletion of embeddings from chroma DB
        return GenericResponse(status="success", message=f"{book_name} deleted")
    
    raise HTTPException(status_code=404, detail="Book not found")
