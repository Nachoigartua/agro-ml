"""Dependency injection para FastAPI."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Request

from .clients.mock_main_system_client import MockMainSystemAPIClient
from .db.persistence import PersistenceContext
from .services.siembra.recommendation_service import SiembraRecommendationService


async def get_persistence_context() -> AsyncGenerator[PersistenceContext, None]:
    """Proporciona el contexto de persistencia con repositorios.
    
    PersistenceContext crea su propia sesión internamente usando el session_factory.
    """
    async with PersistenceContext() as context:
        yield context


async def get_main_system_client(request: Request) -> MockMainSystemAPIClient:
    """Proporciona el cliente del sistema principal.
    
    TODO: Cambiar a MainSystemAPIClient cuando se implemente la API real.
    Para cambiar entre mock y real, modificar el import y la clase retornada.
    """
    # Por ahora usamos el mock
    return MockMainSystemAPIClient(request=request)


async def get_siembra_service(
    client: MockMainSystemAPIClient = Depends(get_main_system_client),
) -> SiembraRecommendationService:
    """Proporciona el servicio de recomendaciones de siembra."""
    return SiembraRecommendationService(
        main_system_client=client,
        persistence_context_factory=PersistenceContext,
    )
