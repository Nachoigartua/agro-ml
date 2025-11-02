"""Cliente para la API del sistema principal (mock local)."""
from __future__ import annotations

from typing import Dict, Optional
from uuid import UUID

from fastapi import Request

from ..core.logging import get_logger


logger = get_logger("main_system_client")


LOTES_DB: Dict[str, Dict[str, object]] = {
    "c3f2f1ab-ca2e-4f8b-9819-377102c4d889": {
        "lote_id": "c3f2f1ab-ca2e-4f8b-9819-377102c4d889",
        "nombre": "Lote Pergamino Norte",
        "establecimiento_id": "est-123",
        "superficie_ha": 120,
        "ubicacion": {"latitud": -33.89, "longitud": -60.57},
        "suelo": {
            "tipo_suelo": "argiudol",
            "ph_suelo": 6.5,
            "materia_organica": 3.2,
            "materia_organica_pct": 3.2,
        },
        "clima": {
            "temp_media_marzo": 21.0,
            "temp_media_abril": 17.0,
            "temp_media_mayo": 13.0,
            "precipitacion_marzo": 120.0,
            "precipitacion_abril": 90.0,
            "precipitacion_mayo": 60.0,
        },
    },
    "f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30": {
        "lote_id": "f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30",
        "nombre": "Lote Sur Córdoba",
        "ubicacion": {"latitud": -33.6, "longitud": -63.8},
        "suelo": {
            "tipo_suelo": "franco arenosa",
            "ph_suelo": 6.2,
            "materia_organica": 2.1,
            "materia_organica_pct": 2.1,
        },
        "clima": {
            "temp_media_marzo": 22.0,
            "temp_media_abril": 18.0,
            "temp_media_mayo": 14.0,
            "precipitacion_marzo": 100.0,
            "precipitacion_abril": 80.0,
            "precipitacion_mayo": 50.0,
        },
    },
    "a17c9db2-5588-4b71-8f8a-6a54b1ad7eaa": {
        #se agrego para probar riesgos, deberia saltar riesgo de heladas y poca lluvia
        "lote_id": "a17c9db2-5588-4b71-8f8a-6a54b1ad7eaa",
        "nombre": "Lote Cordillera Neuquén",
        "establecimiento_id": "est-456",
        "superficie_ha": 85,
        "ubicacion": {"latitud": -39.5, "longitud": -70.6},  # Nequen, frio y poca lluvia
        "suelo": {
            "tipo_suelo": "andisol volcánico",
            "ph_suelo": 5.8,
            "materia_organica": 6.1,
            "materia_organica_pct": 6.1,
        },
        "clima": {
            "temp_media_marzo": 12.0,
            "temp_media_abril": 7.0,
            "temp_media_mayo": 3.0,
            "precipitacion_marzo": 70.0,
            "precipitacion_abril": 55.0,
            "precipitacion_mayo": 40.0,
        },
        "cultivo_anterior": "trigo",
    },
}


class MainSystemAPIClient:
    """Cliente mock que simula la API del sistema principal."""

    def __init__(self, base_url: str, request: Optional[Request] = None):
        self.base_url = base_url
        self._request = request

    @property
    def auth_token(self) -> Optional[str]:
        """Obtiene el token de autenticación del request actual."""

        if self._request and getattr(self._request.state, "user", None):
            return self._request.state.user.get("token")
        return None
        
    async def get_lote_data(self, lote_id: str) -> Dict:
        """Obtiene datos del lote desde el sistema principal."""
        #TODO: Implementar la llamada real a la API del sistema principal
        return LOTES_DB.get(lote_id)

        
