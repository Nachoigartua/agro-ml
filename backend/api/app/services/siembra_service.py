"""Servicio de recomendaciones de siembra."""
from __future__ import annotations

from datetime import datetime

from ..clients.main_system_client import MainSystemAPIClient
from ..dto.siembra import (
    SiembraRecommendationResponse, 
    SiembraRequest,
    RecomendacionBase
)


class SiembraRecommendationService:
    """Servicio para generar recomendaciones de siembra."""

    def __init__(self, main_system_client: MainSystemAPIClient):
        self.main_system_client = main_system_client

    async def generate_recommendation(
        self, request: SiembraRequest
    ) -> SiembraRecommendationResponse:
        """
        Genera una recomendación de siembra para un lote específico.
        """
        # TODO: Implementar la request completa al sistema principal
        lote_data = await self.main_system_client.get_lote_data(request.lote_id)
        
        # TODO: Validar que el lote pertenezca al cliente

        # Crear recomendación principal con datos mock
        recomendacion_principal = RecomendacionBase(
            cultivo=request.cultivo,
            fecha_siembra=datetime.now(),
            densidad_siembra=80.0,  # kg/ha
            profundidad_siembra=5.0,  # cm
            espaciamiento_hileras=17.5,  # cm
            score=0.85
        )

        return SiembraRecommendationResponse(
            lote_id=request.lote_id,
            tipo_recomendacion="siembra",
            recomendacion_principal=recomendacion_principal,
            alternativas=[],  # Lista vacía por ahora
            nivel_confianza=0.85,
            factores_considerados=["humedad_suelo", "temperatura"],
            costos_estimados={"semilla": 100.0, "laboreo": 50.0},
            fecha_generacion=datetime.now()
        )
    