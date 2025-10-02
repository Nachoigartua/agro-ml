from functools import lru_cache
from fastapi import Depends

from .clients.main_system_client import MainSystemAPIClient
from .services.siembra_service import SiembraRecommendationService


@lru_cache
def get_main_system_client() -> MainSystemAPIClient:
    """Provider del cliente del sistema principal."""
    return MainSystemAPIClient(base_url="http://sistema-principal/api")


def get_siembra_service(
    main_system_client: MainSystemAPIClient = Depends(get_main_system_client),
) -> SiembraRecommendationService:
    """Provider del servicio de recomendaciones de siembra."""
    return SiembraRecommendationService(main_system_client=main_system_client)
