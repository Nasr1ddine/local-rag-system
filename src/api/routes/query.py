import logging
from fastapi import APIRouter, HTTPException, Request
from src.models.schemas import QueryRequest, QueryResponse, SourceDocument
from src.core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])

@router.post("", response_model=QueryResponse)
async def query_system(request: QueryRequest, app_req: Request):
    """
    Retrieves chunks based on the query and generates an answer using Ollama.
    Relies on app.state.pipeline being initialized on startup.
    """
    logger.info(f"Processing query: {request.question}")
    try:
        pipeline: RAGPipeline = app_req.app.state.pipeline
        
        # We need the pipeline to return structured data to form the response
        # Currently pipeline.query(question) returns a string. 
        # We will wrap it, or modify the RAGPipeline directly later if needed.
        # For now, let's call the pipeline's retriever to get exact sources first
        
        retriever = pipeline.retriever
        chunks = retriever.retrieve(request.question, top_k=request.top_k)
        
        sources = []
        image_urls = []
        
        for chunk in chunks:
            # Map chunk data into SourceDocument schema
            metadata = chunk.get("metadata", {})
            sources.append(
                SourceDocument(
                    book=metadata.get("book", "Unknown"),
                    page=metadata.get("page", 0),
                    chunk_id=chunk.get("id", "Unknown")
                )
            )
            # Find associated images
            if "image_refs" in metadata and metadata["image_refs"]:
                import json
                try:
                    refs = json.loads(metadata["image_refs"]) if isinstance(metadata["image_refs"], str) else metadata["image_refs"]
                    # Format as accessible URL path
                    base_url = str(app_req.base_url).rstrip("/")
                    for img in refs:
                        # Convert data/images/something.png into base_url/images/something.png
                        img_path = img.split("data/images/")[-1] if "data/images/" in img else img
                        image_urls.append(f"{base_url}/images/{img_path}")
                except Exception as e:
                    logger.error(f"Failed to parse image_refs: {e}")
                
        # Get textual answer
        answer = pipeline.query(request.question)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            images=list(set(image_urls)) # deduplicate
        )
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
