"""
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "use_mock_data": settings.USE_MOCK_DATA
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint
    """
    # Check database connection
    from database.connection import check_db_connection
    db_healthy = await check_db_connection()
    
    # Check Redis connection
    from services.cache_service import cache_service
    redis_healthy = await cache_service.ping()
    
    is_ready = db_healthy and redis_healthy
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }