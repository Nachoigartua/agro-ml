"""
Main FastAPI application for Agro ML System
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from config import settings
from api.routes import ml_routes, health, finnegans_mock
from utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    logger.info(f"Starting Agro ML API in {settings.ENVIRONMENT} mode")
    logger.info(f"Using mock data: {settings.USE_MOCK_DATA}")
    
    from database.connection import init_db
    await init_db()
    
    from services.prediction_service import prediction_service
    await prediction_service.initialize()
    
    logger.info("Agro ML API started successfully")
    
    yield
    
    logger.info("Shutting down Agro ML API")
    from database.connection import close_db
    await close_db()


app = FastAPI(
    title="Agro ML API",
    description="Sistema de Machine Learning para Optimización Agrícola",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "An error occurred",
            "path": str(request.url)
        }
    )


app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(ml_routes.router, prefix="/api/ml", tags=["ML"])

if settings.USE_MOCK_DATA:
    app.include_router(finnegans_mock.router, prefix="/api/mock", tags=["Mock"])
    logger.info("Mock data endpoints enabled")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )