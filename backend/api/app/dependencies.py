from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.persistence import PersistenceContext
from app.db.session import get_db_session as _get_db_session

from .clients.main_system_client import MainSystemAPIClient
from .services.siembra_service import SiembraRecommendationService


def get_main_system_client(request: Request) -> MainSystemAPIClient:
    """Crea un cliente del sistema principal acoplado al request actual."""
    return MainSystemAPIClient(base_url="http://sistema-principal/api", request=request)


async def get_persistence_context() -> AsyncIterator[PersistenceContext]:
    """Entrega un contexto de persistencia que maneja commit/rollback automático."""

    async with PersistenceContext() as context:
        yield context


def get_siembra_service(
    main_system_client: MainSystemAPIClient = Depends(get_main_system_client),
    persistence: PersistenceContext = Depends(get_persistence_context),
) -> SiembraRecommendationService:
    """Entrega una instancia del servicio de recomendaciones de siembra."""
    return SiembraRecommendationService(
        main_system_client=main_system_client,
        persistence_context=persistence,
    )


async def get_database_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency que provee una sesión de base de datos."""

    async for session in _get_db_session():
        yield session
