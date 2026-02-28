from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str
    ollama: str
    vector_store: str

class IngestUrlRequest(BaseModel):
    url: HttpUrl

class IngestResponse(BaseModel):
    status: str
    book: str
    chunks_added: int

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class SourceDocument(BaseModel):
    book: str
    page: int
    chunk_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    images: List[str]

class BookListResponse(BaseModel):
    books: List[str]

class GenericResponse(BaseModel):
    status: str
    message: str
