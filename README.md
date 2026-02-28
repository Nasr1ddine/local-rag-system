# Local RAG System

A fully local, production-quality Retrieval-Augmented Generation (RAG) system that ingests PDF books and answers questions with precise source attribution — no cloud, no internet required after setup.

---

## Features

- 📄 **PDF ingestion** — from local files or URLs
- 🔍 **Semantic search** — embeddings via Ollama (`nomic-embed-text`)
- 🤖 **Local LLM** — question answering via Ollama (`llama3.1`)
- 🗃️ **Vector store** — persistent ChromaDB
- 🌐 **REST API** — FastAPI with interactive Swagger docs
- 🖼️ **Image extraction** — images from PDFs served statically

---

## Project Structure

```
rag_system/
├── src/
│   ├── api/
│   │   ├── main.py            # FastAPI app entry point
│   │   └── routes/
│   │       ├── health.py
│   │       ├── books.py
│   │       ├── ingest.py
│   │       └── query.py
│   ├── core/
│   │   ├── config.py          # Paths & model config
│   │   ├── rag_pipeline.py
│   │   ├── ollama_client.py
│   │   └── citation_handler.py
│   ├── ingestion/
│   │   ├── downloader.py
│   │   ├── parser.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   └── image_extractor.py
│   ├── storage/
│   │   └── chroma_store.py
│   └── models/
│       └── schemas.py
├── data/
│   ├── raw_pdfs/              # Drop PDFs here
│   └── processed/
├── vector_store/              # ChromaDB persisted data
├── main.py                    # CLI interface
└── requirements.txt
```

---

## Prerequisites

- [Ollama](https://ollama.com) installed and running
- Required models pulled:
  ```bash
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```

---

## Setup

```bash
# 1. Create and activate virtual environment (using uv recommended)
uv venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the API server (from the rag_system/ directory)
cd rag_system
python -m uvicorn src.api.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/books` | List all ingested books |
| `DELETE` | `/books/{book_name}` | Delete a book |
| `POST` | `/ingest/file` | Upload a PDF file |
| `POST` | `/ingest/url` | Ingest a PDF from URL |
| `POST` | `/query` | Ask a question |

Interactive docs: **http://127.0.0.1:8000/docs**

---

## CLI Usage

```bash
# Ingest PDFs from a folder
python main.py ingest --source ./data/raw_pdfs

# Download and ingest from URL
python main.py ingest --source https://example.com/book.pdf

# Generate embeddings
python main.py embed

# Query the system
python main.py query "What is the main argument of the book?"
```

---

## Configuration

Edit `src/core/config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_MODEL` | `llama3.1` | Ollama model for answering |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model for embeddings |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Number of chunks retrieved per query |
