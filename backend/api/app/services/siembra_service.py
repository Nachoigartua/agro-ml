"""Servicio de recomendaciones de siembra."""
from __future__ import annotations

from datetime import datetime, timedelta

from ..clients.main_system_client import MainSystemAPIClient
from ..dto.siembra import SiembraRecommendationResponse, SiembraRequest


class SiembraRecommendationService:
    """Servicio para generar recomendaciones de siembra."""

    def __init__(self, main_system_client: MainSystemAPIClient):
        self.main_system_client = main_system_client

    async def generate_recommendation(
        self, request: SiembraRequest
    ) -> SiembraRecommendationResponse:
        """Genera una recomendación de siembra para un lote específico."""
        # TODO: Implementar la request completa al sistema principal
        _ = await self.main_system_client.get_lote_data(request.lote_id)

        # TODO: Validar que el lote pertenezca al cliente

        # Crear recomendación principal con datos mock
        now = datetime.utcnow()
        fecha_optima = now + timedelta(days=7)
        ventana_inicio = (fecha_optima - timedelta(days=5)).date().isoformat()
        ventana_fin = (fecha_optima + timedelta(days=5)).date().isoformat()

        recomendacion_principal = {
            "fecha_optima": fecha_optima.date().isoformat(),
            "ventana": [ventana_inicio, ventana_fin],
            "confianza": 0.85,
        }

        alternativas = [
            {
                "fecha": (fecha_optima + timedelta(days=10)).date().isoformat(),
                "pros": ["Mayor humedad esperada"],
                "contras": ["Riesgo de heladas tardías"],
                "confianza": 0.72,
            }
        ]

        return SiembraRecommendationResponse(
            lote_id=request.lote_id,
            tipo_recomendacion="siembra",
            recomendacion_principal=recomendacion_principal,
            alternativas=alternativas,
            nivel_confianza=0.85,
            factores_considerados=["humedad_suelo", "temperatura"],
            costos_estimados={"semilla": 100.0, "laboreo": 50.0},
            fecha_generacion=datetime.utcnow(),
            cultivo=request.cultivo,
        )
