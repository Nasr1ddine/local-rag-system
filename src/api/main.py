from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from src.api.routes import health, books, ingest, query
from src.core.config import ensure_directories, IMAGES_DIR
from src.core.rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Local RAG System", description="API for Local RAG using FastAPI and Ollama")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    ensure_directories()
    logger.info("Initializing RAG Pipeline (loads Vector Store)...")
    app.state.pipeline = RAGPipeline()
    logger.info("Application startup complete.")

app.include_router(health.router)
app.include_router(books.router)
app.include_router(ingest.router)
app.include_router(query.router)

ensure_directories()
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
