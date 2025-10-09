import logging

from fastapi import APIRouter, status

from ..dto.health import HealthStatusResponse


logger = logging.getLogger("agro_ml.health")

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def health_check() -> HealthStatusResponse:
    """Endpoint simple de salud para el dashboard."""
    logger.debug("Health check solicitado")
    return HealthStatusResponse()

