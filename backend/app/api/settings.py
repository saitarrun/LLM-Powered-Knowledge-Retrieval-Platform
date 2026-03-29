"""Settings and configuration routes."""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["settings"])

@router.get("/settings")
async def get_settings():
    """Get application settings."""
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_v1_str": settings.API_V1_STR,
        "embedding_model": settings.EMBEDDING_MODEL,
        "log_level": settings.LOG_LEVEL
    }

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }
