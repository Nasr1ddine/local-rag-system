from fastapi import APIRouter
from src.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        ollama="connected",
        vector_store="loaded"
    )
