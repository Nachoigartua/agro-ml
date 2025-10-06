from functools import lru_cache
import os
from typing import Optional

from fastapi import Depends, Request

from .clients.main_system_client import MainSystemAPIClient
from .services.siembra_service import SiembraRecommendationService

try:  # pragma: no cover - entornos sin redis instalado
    from redis.asyncio import Redis  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Redis = None  # type: ignore


def get_main_system_client(request: Request) -> MainSystemAPIClient:
    """Provider del cliente del sistema principal (scope por request)."""
    return MainSystemAPIClient(base_url="http://sistema-principal/api", request=request)


@lru_cache
def get_redis_client() -> Optional[object]:
    """Provider de conexión Redis (opcional en desarrollo)."""
    if Redis is None:
        return None
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        return Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - configuración inválida
        return None


def get_siembra_service(
    main_system_client: MainSystemAPIClient = Depends(get_main_system_client),
    redis_client: Optional[object] = Depends(get_redis_client),
) -> SiembraRecommendationService:
    """Provider del servicio de recomendaciones de siembra."""
    return SiembraRecommendationService(
        main_system_client=main_system_client,
        redis_client=redis_client,
    )
