from fastapi import APIRouter
from backend.core.config import get_settings
from backend.db.database import check_db_health

router = APIRouter()
settings = get_settings()


@router.get("")
def health_check():
    """
    Returns application health, database status, and active AI configurations.
    """
    db_status = check_db_health()
    return {
        "status": "healthy" if db_status.get("connected") else "degraded",
        "database": db_status,
        "default_ai_provider": settings.DEFAULT_AI_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "web_search_provider": settings.WEB_SEARCH_PROVIDER,
        "storage_dir": settings.STORAGE_DIR,
    }

