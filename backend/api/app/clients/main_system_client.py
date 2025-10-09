"""Cliente para la API del sistema principal (mock local)."""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import Request

from ..core.logging import get_logger


logger = get_logger("main_system_client")


LOTES_DB: Dict[str, Dict[str, object]] = {
    "lote-001": {
        "lote_id": "lote-001",
        "nombre": "Lote Pergamino Norte",
        "establecimiento_id": "est-123",
        "superficie_ha": 120,
        "ubicacion": {"latitud": -33.89, "longitud": -60.57},
        "suelo": {"tipo_suelo": "argiudol", "ph_suelo": 6.5, "materia_organica": 3.2},
        "cultivo_anterior": "soja",
    },
    "lote-002": {
        "lote_id": "lote-002",
        "nombre": "Lote Sur Córdoba",
        "ubicacion": {"latitud": -33.6, "longitud": -63.8},
        "suelo": {"tipo_suelo": "franco arenosa", "ph_suelo": 6.2, "materia_organica": 2.1},
        "cultivo_anterior": "maiz",
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

        
