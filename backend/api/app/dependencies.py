from fastapi import Depends, Request

from .clients.main_system_client import MainSystemAPIClient
from .services.siembra_service import SiembraRecommendationService


def get_main_system_client(request: Request) -> MainSystemAPIClient:
    """Provider del cliente del sistema principal (con alcance por request)."""
    return MainSystemAPIClient(base_url="http://sistema-principal/api", request=request)


def get_siembra_service(
    main_system_client: MainSystemAPIClient = Depends(get_main_system_client),
) -> SiembraRecommendationService:
    """Provider del servicio de recomendaciones de siembra."""
    return SiembraRecommendationService(main_system_client=main_system_client)

