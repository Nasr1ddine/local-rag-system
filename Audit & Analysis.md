### 1. Repository Overview

- **Purpose**  
  This project is a **fully local Retrieval-Augmented Generation (RAG) system** for PDF books. It ingests PDFs, extracts text and images, chunks and embeds them into a **persistent ChromaDB vector store**, and serves a **FastAPI REST API** (and a CLI) that answers questions using a local **Ollama LLM**, with **explicit source citations** and image references.

- **Problem it solves**  
  It lets you:
  - Ingest PDFs from local folders or URLs  
  - Run **semantic search + LLM QA** entirely locally (no external cloud services once set up)  
  - Get answers with **(Book, Page)** citations and **image links** for transparency and trust.

- **Tech stack & frameworks**
  - **Language**: Python 3.11
  - **Web framework**: FastAPI + Uvicorn
  - **CLI**: Typer
  - **Vector store**: ChromaDB (persistent, via `chromadb`)
  - **LLM & embeddings**: Ollama (`llama3.1` for generation, `nomic-embed-text` for embeddings)
  - **PDF parsing**: PyMuPDF (`fitz`)
  - **Text splitting**: `langchain-text-splitters` (RecursiveCharacterTextSplitter)
  - **Validation / schemas**: Pydantic v2
  - **Containerization**: Dockerfile + `docker-compose.yml` (runs API + Ollama as services)

---

### 2. Project Architecture

- **Architectural pattern**
  - Overall: **Layered architecture** with a clear separation:
    - **API layer** (`src/api`): HTTP endpoints and wiring to the pipeline.
    - **Core RAG logic** (`src/core`): config, pipeline, retriever, prompt builder, LLM client, citation formatting.
    - **Ingestion layer** (`src/ingestion`): downloading, parsing, chunking, embedding.
    - **Storage layer** (`src/storage`): vector store (ChromaDB).
    - **Schemas** (`src/models`): Pydantic models for API contracts.
  - Access style: The **API and CLI** are thin orchestrators that call into shared core/ingestion/storage modules.

- **Main component interactions**
  - **Ingestion pipeline** (CLI or API `/ingest`):
    1. `PDFDownloader` → pulls PDFs into `data/raw_pdfs` and maintains a registry.
    2. `PDFParser` (+ `ImageExtractor`) → parses text + images into `data/processed/text` JSON and `data/processed/images`.
    3. `TextChunker` → splits parsed text pages into overlapping chunks with metadata.
    4. `VectorStore` (+ `Embedder`) → embeds chunks via Ollama and persists them in ChromaDB.
  - **Query pipeline**:
    1. `Retriever` → queries `VectorStore` with embedding of the question.
    2. `PromptBuilder` → builds a context-packed prompt with book/page/image info.
    3. `OllamaClient` → sends system + user prompt to Ollama.
    4. `CitationHandler` → formats answer with `SOURCES:` and `IMAGES:` sections.
    5. API `/query` wraps this answer plus structured `SourceDocument` and image URLs.

---

### 3. Folder-by-Folder Explanation

- **Project root**
  - **Purpose**: Project configuration, entrypoints, containerization.
  - **Key contents**:
    - `main.py` – CLI entrypoint.
    - `requirements.txt` – Python dependencies.
    - `Dockerfile` – build/run API container.
    - `docker-compose.yml` – run API + Ollama together.
    - `.env.example` – sample configuration.
    - `README.md` – project overview and usage docs.
    - `vector_store/` – on-disk ChromaDB data.
    - `data/` (described via config/README) – raw and processed ingestion data.

- **`src/`**
  - **Purpose**: All application source code.
  - Subfolders:
    - `src/api/` – FastAPI app and route modules.
    - `src/core/` – core configuration and RAG pipeline logic.
    - `src/ingestion/` – code that ingests and preprocesses PDFs.
    - `src/storage/` – vector store abstraction (ChromaDB).
    - `src/models/` – Pydantic schema definitions.

- **`src/api/`**
  - **Purpose**: HTTP API layer.
  - Files:
    - `main.py` – FastAPI app creation, middleware, mounting routes, startup pipeline initialization, static image mounting.
    - `routes/` – per-feature routers: `health.py`, `books.py`, `ingest.py`, `query.py`.

- **`src/core/`**
  - **Purpose**: Central RAG logic and configuration.
  - Files:
    - `config.py` – paths, environment-driven tunables, model settings, `ensure_directories()`.
    - `rag_pipeline.py` – `RAGPipeline` orchestration of retrieve → prompt → generate → format.
    - `retriever.py` – retrieval from Chroma vector store.
    - `prompt_builder.py` – builds the system + user prompt.
    - `ollama_client.py` – client wrapper around `ollama.Client`.
    - `citation_handler.py` – formats answer + sources + image references.

- **`src/ingestion/`**
  - **Purpose**: ETL for PDFs.
  - Files:
    - `downloader.py` – handles PDF registration, local directory ingest, and HTTP download.
    - `parser.py` – parses PDFs into JSON pages with text + image refs.
    - `chunker.py` – splits parsed pages into chunks for embedding.
    - `embedder.py` – talks to Ollama embeddings API.
    - `image_extractor.py` – saves per-page images to disk and returns metadata.

- **`src/storage/`**
  - **Purpose**: Vector store abstraction.
  - Files:
    - `chroma_store.py` – `VectorStore` around `chromadb.PersistentClient`.

- **`src/models/`**
  - **Purpose**: API data models.
  - Files:
    - `schemas.py` – Pydantic models: health, ingest, query, books, generic responses.

- **Data directories (from `config.py` and README)**
  - `data/raw_pdfs/` – source PDFs you ingest.
  - `data/processed/`:
    - `text/` – JSON outputs from `PDFParser`.
    - `images/` – extracted images, by book.
    - `metadata/` – auxiliary JSON (`pdf_registry.json`, etc.).
  - `vector_store/` – ChromaDB persistent database.
  - `models/` – optional directory for local model-related assets.

---

### 4. File-by-File Explanation (Key Behavior & Interactions)

#### Root

- **`README.md`**
  - Explains features, structure, prerequisites, setup (venv, pip, uvicorn), API endpoints, CLI usage, and configurable settings mapping directly to `src/core/config.py`.

- **`requirements.txt`**
  - **fastapi**, **uvicorn** – API server.
  - **pymupdf (fitz)** – PDF parsing & image extraction.
  - **langchain-text-splitters** – chunking.
  - **chromadb** – vector store.
  - **ollama** – Python client to Ollama.
  - **pydantic** – data models.
  - **typer** – CLI.

- **`main.py`** (CLI)

  ```startLine: endLine:filepath
  1:77:main.py
  ```

  - Defines a `typer.Typer` app with commands:
    - `ingest(source: str = None)`:  
      - Calls `ensure_directories()` from `config.py`.  
      - Instantiates `PDFDownloader`.  
      - If `source` is a directory: calls `ingest_local_directory(source_path)`.  
      - If `source` is a URL: calls `download_from_urls([source])`.  
      - Then runs `PDFParser().parse_all_pdfs()` to produce parsed JSON.
    - `embed()`:  
      - Calls `ensure_directories()`.  
      - Creates `TextChunker`, calls `chunk_all_parsed_files()`.  
      - If chunks exist, creates `VectorStore` and calls `add_chunks(chunks)`.
    - `query(question: str)`:  
      - Calls `ensure_directories()`.  
      - Instantiates `RAGPipeline`, calls `pipeline.query(question)` and prints the formatted output.
  - **Entry point**: `if __name__ == "__main__": ensure_directories(); app()`.

- **`Dockerfile`**

  ```startLine: endLine:filepath
  1:49:Dockerfile
  ```

  - **Stage 1 (builder)**: installs dependencies into `/install`.
  - **Stage 2 (runtime)**:
    - Copies installed site-packages and application source (`src`, `main.py`).
    - Creates needed data directories.
    - Runs as `appuser` (non-root) for security.
    - Exposes port 8000 and starts Uvicorn with `src.api.main:app`.

- **`docker-compose.yml`**

  ```startLine: endLine:filepath
  1:43:docker-compose.yml
  ```

  - `api` service:
    - Builds from current context (using `Dockerfile`).
    - Sets `OLLAMA_HOST`, model names, chunking and retrieval params from env.
    - Mounts volumes for `data` and `vector_store`.
    - Depends on `ollama` healthcheck.
  - `ollama` service:
    - Runs official `ollama/ollama` image, exposes 11434.
    - Persists models in `ollama_models` volume, with healthcheck.

- **`.env.example`**
  - Documents environment vars for port, Ollama host, model names, and RAG tuning (chunk size, overlap, top-k).

#### `src/api`

- **`src/api/main.py`**

  ```startLine: endLine:filepath
  1:40:src/api/main.py
  ```

  - Creates `FastAPI` app with title/description.
  - Adds **CORS middleware** allowing all origins, credentials, methods, headers.
  - `@app.on_event("startup")`:
    - Calls `ensure_directories()`.
    - Instantiates `RAGPipeline` and stores it on `app.state.pipeline`.  
      This is the shared pipeline used by routes for querying.
  - `include_router(...)` for:
    - `health`, `books`, `ingest`, `query`.
  - Mounts **static images** at `/images` using `IMAGES_DIR`.
  - `if __name__ == "__main__"` allows running via `python src/api/main.py`.

- **`src/api/routes/health.py`**

  ```startLine: endLine:filepath
  1:12:src/api/routes/health.py
  ```

  - Defines `/health` GET route returning `HealthResponse`.
  - Currently **hardcodes** `status="ok"`, `ollama="connected"`, `vector_store="loaded"` (no actual runtime checks).

- **`src/api/routes/books.py`**

  ```startLine: endLine:filepath
  1:26:src/api/routes/books.py
  ```

  - `/books` GET:
    - Lists all `*.pdf` filenames in `RAW_PDF_DIR`.
  - `/books/{book_name}` DELETE:
    - Deletes a PDF from `RAW_PDF_DIR`.
    - TODO: does *not* yet delete corresponding embeddings from Chroma.

- **`src/api/routes/ingest.py`**

  ```startLine: endLine:filepath
  1:75:src/api/routes/ingest.py
  ```

  - Defines local helper `process_pdf(file_path_or_url: str)`, which:
    - Creates `PDFDownloader`.
    - If the string starts with `http`: `download_from_urls`.
    - Else: `ingest_local_directory(RAW_PDF_DIR)` (meaning the path is used mostly as a trigger; this ingests whatever is in `RAW_PDF_DIR`).
    - Runs `PDFParser().parse_all_pdfs()`.
    - Runs `TextChunker().chunk_all_parsed_files()`.
    - If chunks exist, creates `VectorStore` and calls `add_chunks(chunks)`.
  - `/ingest/file` POST:
    - Accepts `UploadFile` for a PDF.
    - Saves to `RAW_PDF_DIR`.
    - Submits `process_pdf` as a FastAPI `BackgroundTasks` job.
    - Returns `IngestResponse` with `chunks_added=0` (since actual count is async).
  - `/ingest/url` POST:
    - Accepts `IngestUrlRequest` with a URL.
    - Submits `process_pdf(url)` in the background.
    - Returns `IngestResponse` similarly.

- **`src/api/routes/query.py`**

  ```startLine: endLine:filepath
  1:65:src/api/routes/query.py
  ```

  - `/query` POST with `QueryRequest` body (`question`, `top_k`).
  - Uses `app_req.app.state.pipeline` to get the shared `RAGPipeline`.
  - **Retrieval for structured response**:
    - Calls `pipeline.retriever.retrieve(request.question, top_k=request.top_k)`.
    - Expects `chunk` structure, but the current implementation assumes a `metadata` dict in each chunk; in reality `Retriever` returns a flat dict (`book`, `page`, `images`, `distance`). So this is somewhat mismatched and would need alignment.
    - Constructs `SourceDocument` entries from metadata (book, page, chunk_id).
    - Builds `image_urls` by interpreting `image_refs` and prefixing with `base_url/images/...`. The logic assumes `image_refs` is JSON or direct paths under `data/images/`.
  - **LLM answer**:
    - Calls `pipeline.query(request.question)`, which returns the **formatted string** (ANSWER + SOURCES + IMAGES) from `CitationHandler`.
    - Returns `QueryResponse` with:
      - `answer`: that formatted string.
      - `sources`: structured list (potentially redundant with the text `SOURCES:`).
      - `images`: deduplicated `image_urls`.

#### `src/core`

- **`config.py`**

  ```startLine: endLine:filepath
  1:43:src/core/config.py
  ```

  - Computes key paths relative to the project root (`BASE_DIR`).
  - Config variables:
    - `LLM_MODEL`, `EMBEDDING_MODEL` from env (default `llama3.1`, `nomic-embed-text`).
    - `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_RETRIEVAL` from env (with defaults).
    - `OLLAMA_HOST` from env (`http://localhost:11434` by default).
  - `ensure_directories()` – creates `data/raw_pdfs`, processed dirs, `vector_store`, `models`.

- **`rag_pipeline.py`**

  ```startLine: endLine:filepath
  1:37:src/core/rag_pipeline.py
  ```

  - `RAGPipeline` composes:
    - `Retriever` (Chroma retrieval),
    - `PromptBuilder`,
    - `OllamaClient`,
    - `CitationHandler`.
  - `query(user_question: str) -> str`:
    1. Calls `retriever.retrieve(user_question)`. If no chunks, returns a fixed no-context message.
    2. Uses `PromptBuilder.system_prompt` and `build_prompt` with question + chunks.
    3. Invokes `OllamaClient.generate(system_prompt, user_prompt)` to get the answer string.
    4. Calls `CitationHandler.format_final_output(answer, retrieved_chunks)` to add `SOURCES:` and `IMAGES:`.

- **`retriever.py`**

  ```startLine: endLine:filepath
  1:40:src/core/retriever.py
  ```

  - Wraps `VectorStore`.
  - `retrieve(query: str, top_k: int) -> List[Dict]`:
    - Calls `vector_store.query(query, n_results=top_k)`.
    - Expects Chroma’s `results` dict: `documents`, `metadatas`, `distances`.
    - Maps each entry into:
      - `text`, `book`, `page`, `images`, `distance`.
      - `images` is parsed from `metadata["image_refs"]` as a comma-separated list.

- **`ollama_client.py`**

  ```startLine: endLine:filepath
  1:27:src/core/ollama_client.py
  ```

  - Thin wrapper around `ollama.Client(host=OLLAMA_HOST)`.
  - `generate(system_prompt, user_prompt)`:
    - Sends a chat request with two messages: system and user.
    - Returns `response['message']['content']`, or an error string on failure.

- **`prompt_builder.py`**

  ```startLine: endLine:filepath
  1:35:src/core/prompt_builder.py
  ```

  - Encodes **LLM behavior rules** as `system_prompt`:
    - Only answer from provided context.
    - Use `(Book Name, Page X)` format for citations.
    - Admit when unsure.
  - `build_prompt(query, retrieved_chunks)`:
    - Renders each chunk as:
      - `[Book: {book}, Page: {page}]`
      - `Text: ...`
      - `Image: ...` lines for each image path.
    - Builds a single string: `"Context Information:\n... User Question: ...\n\nAnswer:"`.

- **`citation_handler.py`**

  ```startLine: endLine:filepath
  1:35:src/core/citation_handler.py
  ```

  - `extract_images_from_chunks(chunks)`:
    - Collects all non-empty `images` entries from chunks.
  - `format_final_output(answer, chunks)`:
    - Builds a sorted set of `sources` from `chunk['book']`, `chunk['page']`.
    - Appends to answer:
      - `SOURCES:` section (`* Book, Page N` lines).
      - Optional `IMAGES:` section listing image paths.

#### `src/storage`

- **`chroma_store.py`**

  ```startLine: endLine:filepath
  1:70:src/storage/chroma_store.py
  ```

  - Initializes `chromadb.PersistentClient` at `VECTOR_STORE_DIR`.
  - `collection = get_or_create_collection("rag_documents")`.
  - Also instantiates an `Embedder`.
  - `add_chunks(chunks: List[Dict])`:
    - Short-circuits if empty.
    - Uses `collection.get(ids=[...])` to find existing ids and avoid duplicates.
    - Generates embeddings with `Embedder.generate_embeddings_batch`.
    - Builds `metadatas` for each chunk:
      - `book`, `page`, `chunk_id`, `source_file`, `image_refs` (comma-separated relative paths from image refs).
    - Adds in batches of 5000 to the collection (`ids`, `embeddings`, `metadatas`, `documents`).
  - `query(query_text, n_results)`:
    - Gets a single query embedding via `Embedder.generate_embedding`.
    - Calls `collection.query(query_embeddings=[...], n_results=n_results)`.
    - Returns Chroma’s result dict.

#### `src/ingestion`

- **`downloader.py`**

  ```startLine: endLine:filepath
  1:115:src/ingestion/downloader.py
  ```

  - Tracks all PDFs via `pdf_registry.json` under `METADATA_DIR`.
  - `ingest_local_directory(source_dir)`:
    - Iterates over `*.pdf`, calls `add_file`.
  - `add_file(filepath, original_url=None)`:
    - Validates existence and PDF header.
    - Computes SHA256 checksum and checks registry for duplicates.
    - Copies to `RAW_PDF_DIR`, ensuring no name collision by appending counters.
    - Updates registry with filename, original path/URL, and size.
  - `download_from_urls(urls)`:
    - Downloads each URL to a temporary directory using `urllib.request.urlretrieve`.
    - Then calls `add_file` for each.

- **`parser.py`**

  ```startLine: endLine:filepath
  1:80:src/ingestion/parser.py
  ```

  - `parse_all_pdfs()`:
    - Loops over all PDFs in `RAW_PDF_DIR`.
    - For each, writes a `*_parsed.json` file in `TEXT_DIR`.
    - Skips PDFs already parsed (idempotent).
  - `parse_pdf(pdf_path)`:
    - Uses PyMuPDF `fitz` to open the doc and read TOC.
    - For each page:
      - Extracts plain text.
      - Skips empty pages.
      - Uses `_detect_chapter` to infer chapter name from TOC.
      - Calls `ImageExtractor.extract_images(...)` for images on that page.
      - Records entries with `book_title`, `page_number`, `text`, `images`, and optionally `chapter`.
  - `_detect_chapter(toc, current_page)`:
    - Returns most recent level-1 TOC entry up to `current_page`.

- **`chunker.py`**

  ```startLine: endLine:filepath
  1:68:src/ingestion/chunker.py
  ```

  - Initializes `RecursiveCharacterTextSplitter` with:
    - `chunk_size = CHUNK_SIZE * 4`, `chunk_overlap = CHUNK_OVERLAP * 4`, approximating characters to tokens.
  - `chunk_all_parsed_files()`:
    - For each `*_parsed.json` in `TEXT_DIR`, calls `chunk_file` and aggregates chunks.
  - `chunk_file(parsed_file)`:
    - Loads JSON pages, for each page:
      - Skips empty text.
      - Splits text into chunks.
      - For each chunk:
        - Generates deterministic `chunk_id` via MD5 over book title, page, index, and first 50 characters.
        - Stores `text`, `book`, `page`, `source_file`, `image_refs` (the page’s image list).

- **`embedder.py`**

  ```startLine: endLine:filepath
  1:40:src/ingestion/embedder.py
  ```

  - Wraps `ollama.Client` configured with `EMBEDDING_MODEL`.
  - `generate_embeddings_batch(texts)`:
    - Iterates over texts, calls `client.embeddings(model, prompt=text)`.
    - Returns list of embedding vectors.
  - `generate_embedding(text)`:
    - Same for single string, returning one embedding.

- **`image_extractor.py`**

  ```startLine: endLine:filepath
  1:48:src/ingestion/image_extractor.py
  ```

  - `extract_images(doc, book_name, page_num)`:
    - Loads page, iterates `page.get_images(full=True)`.
    - Uses `doc.extract_image(xref)` to get image bytes and extension.
    - Saves to `IMAGES_DIR / book_name / page{page}_img{n}.{ext}`.
    - Produces list of dicts with `image_path` (relative under `data/processed/images/...`), `book`, `page`, `position`.

#### `src/models`

- **`schemas.py`**

  ```startLine: endLine:filepath
  1:37:src/models/schemas.py
  ```

  - Defines:
    - `HealthResponse` – static health values.
    - `IngestUrlRequest` – body for `/ingest/url`.
    - `IngestResponse` – response for both ingest endpoints.
    - `QueryRequest` – question + `top_k`.
    - `SourceDocument` – book, page, chunk_id.
    - `QueryResponse` – answer text, list of `SourceDocument`, list of image URLs.
    - `BookListResponse` – list of PDF names.
    - `GenericResponse` – simple `status` + `message`.

---

### 5. Execution Flow

#### A. API server startup (`uvicorn src.api.main:app --reload`)

1. **Module import**:
   - Python imports `src.api.main`, which:
     - Creates `app = FastAPI(...)`.
     - Adds CORS middleware.
     - Includes routers.
     - Mounts `/images` to `IMAGES_DIR`.
2. **Startup event** (`@app.on_event("startup")`):
   - Calls `ensure_directories()` – creates data/vector_store/models directories.
   - Builds `RAGPipeline()`:
     - Inside: instantiates `Retriever` → `VectorStore` → `Embedder`.
   - Stores pipeline on `app.state.pipeline`.
3. **Server runs**:
   - Uvicorn serves the app on `0.0.0.0:8000`.

#### B. Ingesting PDFs (API)

- **File upload (`POST /ingest/file`)**:
  1. Validates extension is `.pdf`.
  2. Saves the file to `RAW_PDF_DIR`.
  3. Dispatches `process_pdf(file_path)` in a background task:
     - `PDFDownloader`:
       - If not URL, calls `ingest_local_directory(RAW_PDF_DIR)` (ingests all PDFs in that dir).
     - `PDFParser.parse_all_pdfs()`:
       - For each raw PDF, produces `*_parsed.json` in `TEXT_DIR` plus saved images.
     - `TextChunker.chunk_all_parsed_files()`:
       - For each parsed JSON, splits into chunks with `chunk_id`s.
     - `VectorStore.add_chunks(chunks)`:
       - Embeds with Ollama and writes to Chroma.
  4. Returns immediately with status `success` and `chunks_added=0` (async).

- **URL ingest (`POST /ingest/url`)**:
  - Same pattern, but `process_pdf` sees it’s a URL and uses `download_from_urls`.

- **CLI ingest + embed (`python main.py ingest ...`, `python main.py embed`)**:
  - The CLI offers a **two-step** ingestion:
    - `ingest`: `PDFDownloader` (source folder or URL) + `PDFParser.parse_all_pdfs()`.
    - `embed`: `TextChunker.chunk_all_parsed_files()` + `VectorStore.add_chunks(chunks)`.

#### C. Querying (`POST /query` or CLI `python main.py query "..."`)

- **REST API flow (`/query`)**:
  1. Receives `QueryRequest(question, top_k)`.
  2. Retrieves shared `pipeline` from `app.state.pipeline`.
  3. Uses `pipeline.retriever.retrieve(question, top_k)`:
     - Calls Chroma to get closest chunks by vector similarity.
  4. Builds `sources` and `image_urls` from chunks’ metadata (with some assumptions that may need aligning with current chunk format).
  5. Calls `pipeline.query(question)`:
     - `Retriever` again; then `PromptBuilder` builds a prompt with context; `OllamaClient` gets answer; `CitationHandler` wraps answer.
  6. Returns `QueryResponse` with answer, structured sources, and image URLs.

- **CLI query (`main.py query`)**:
  - Calls `RAGPipeline.query(question)` directly.
  - Prints separator lines, then the formatted answer.

---

### 6. Dependency Analysis

- **External libraries and their roles**
  - **FastAPI / Uvicorn**: API definition and ASGI server.
  - **PyMuPDF (`fitz`)**: PDF reading, TOC extraction, page text, images.
  - **langchain-text-splitters**: smart splitting of long text into overlapping chunks, tuned using chunk_size/overlap.
  - **ChromaDB (`chromadb`)**: persistent vector database for storing embeddings and metadata.
  - **Ollama (`ollama` Python client)**: embedding and generation over local Ollama models.
  - **Pydantic**: typed validation for HTTP request and response bodies.
  - **Typer**: CLI interface with commands for ingest, embed, query.
  - **Standard libs**: `logging`, `hashlib`, `json`, `pathlib`, `urllib.request`, `tempfile`, `asyncio`, `shutil`, etc.

- **Internal dependencies**
  - `main.py` (CLI) depends on:
    - `src.core.config.ensure_directories`, `RAW_PDF_DIR`.
    - `PDFDownloader`, `PDFParser`, `TextChunker`, `VectorStore`.
    - `RAGPipeline`.
  - `src/api/main.py` depends on:
    - Routers (`health`, `books`, `ingest`, `query`).
    - `ensure_directories`, `IMAGES_DIR`.
    - `RAGPipeline`.
  - `RAGPipeline` depends on:
    - `Retriever` → `VectorStore` → `Embedder`.
    - `PromptBuilder`, `OllamaClient`, `CitationHandler`.
  - `VectorStore` depends on:
    - `Embedder`.
    - `config.VECTOR_STORE_DIR`.
  - `Embedder` and `OllamaClient` depend on:
    - `config.OLLAMA_HOST`, `EMBEDDING_MODEL`, `LLM_MODEL`.
  - `PDFDownloader`, `PDFParser`, `ImageExtractor`, `TextChunker` depend on:
    - `config.RAW_PDF_DIR`, `TEXT_DIR`, `IMAGES_DIR`, `METADATA_DIR`.
  - `API routes` depend on:
    - `schemas` for typing,
    - ingestion/core/storage modules for behavior.

---

### 7. Data Flow

- **Ingestion (data in)**:
  - Input:  
    - PDFs (from disk or URLs).
  - Flow:
    1. **Raw PDFs** → `data/raw_pdfs/` (`PDFDownloader`).
    2. **Parsed pages** → `data/processed/text/<book>_parsed.json` (`PDFParser`).
    3. **Images** → `data/processed/images/<book>/pageX_imgY.ext` (`ImageExtractor`).
    4. **Chunks** (list of dicts with text and metadata) created in memory (`TextChunker`).
    5. **Embeddings** → `chromadb` collection `rag_documents` (`VectorStore.add_chunks`).

- **Query (data out)**:
  - Input: User question string.
  - Flow:
    1. Question → embedding via `Embedder.generate_embedding`.
    2. Embedding → similarity search in Chroma → top `k` chunks.
    3. Chunks → `PromptBuilder` renders context with book/page/image info.
    4. Prompts → `OllamaClient` → generated answer.
    5. Answer + chunks → `CitationHandler` → final string with `SOURCES:` and `IMAGES:`.
    6. API adds structured `sources` and `images` URL list around that string for clients.

- **Persistence**
  - **Vector store** in `vector_store/chroma.sqlite3` (and associated Chroma files).
  - **PDF registry** in `data/processed/metadata/pdf_registry.json`.
  - **Parsed pages** and **images** in `data/processed`.

---

### 8. Important Patterns or Design Decisions

- **Design patterns / structure**
  - **Layered architecture**: clear separation between API, core, ingestion, and storage.
  - **Pipeline orchestration**:
    - `RAGPipeline` as a façade over retrieval + generation + formatting.
  - **Dependency inversion**:
    - API interacts with **high-level abstractions** (`RAGPipeline`, `VectorStore`, `PDFDownloader`) rather than low-level details.
  - **Idempotent ingestion**:
    - `PDFDownloader` uses SHA256-based registry to avoid duplicate ingest.
    - `PDFParser` skips already parsed PDFs.
  - **Background tasks**:
    - API ingestion runs heavy work (`process_pdf`) via FastAPI `BackgroundTasks` to keep endpoints responsive.

- **Security considerations**
  - Docker image:
    - Uses a **non-root user** (`appuser`) in runtime stage.
  - CORS:
    - Currently **wide open** (`allow_origins=["*"]`), fine for local/dev but not ideal for locked-down production.
  - File handling:
    - Basic extension check for `/ingest/file` and header check for PDFs in `PDFDownloader`.
    - No explicit rate limiting or auth in the current code.

- **Scalability considerations**
  - Vector store and embeddings:
    - Persistent Chroma allows reusing embeddings across restarts.
    - `VectorStore.add_chunks` uses **batching** (5000 per add).
  - Image storage:
    - Structured per book, enabling serving via static mount and caching/CDN if needed.
  - Compute:
    - Heavy CPU/GPU work (PDF parsing, embeddings, LLM) can be scaled vertically; horizontally scaling requires attention to shared Chroma and Ollama.

---

### 9. Simplified Summary (For a New Developer)

- **What this repo is**  
  A **local question-answering system** over PDFs. You drop in or upload PDFs, it parses them into text and images, stores semantic embeddings in ChromaDB, and then answers questions by retrieving relevant chunks and using a local Ollama LLM, always showing where the answer came from.

- **Main things you’ll interact with**
  - **API**:
    - Start with `uvicorn src.api.main:app --reload`.
    - Hit:
      - `/ingest/file` or `/ingest/url` to ingest content.
      - `/books` to see what’s been ingested.
      - `/query` to ask questions.
  - **CLI**:
    - `python main.py ingest --source ./data/raw_pdfs` to ingest PDFs already in a folder.
    - `python main.py embed` to create embeddings.
    - `python main.py query "Your question"` to query from the terminal.

- **High-level workflow**
  1. **Ingestion**: PDFs → parsed text + images → chunks → embeddings in Chroma.
  2. **Query**: Question → embedding → nearest chunks → prompt → LLM answer → formatted answer with citations and image references.
  3. **Config** (`src/core/config.py` + `.env`): controls data paths, Ollama host, models, and chunking/retrieval parameters.