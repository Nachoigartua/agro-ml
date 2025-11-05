"""Cliente para la API del sistema principal."""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import Request
import httpx

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
        "cultivo_anterior": "soja",
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
        "cultivo_anterior": "maiz",
    },
    "c3f2f1ab-ca2e-4f8b-9819-377102c4d879": {
        "lote_id": "c3f2f1ab-ca2e-4f8b-9819-377102c4d879",
        "nombre": "Lote Pergamino Sur",
        "establecimiento_id": "est-123",
        "superficie_ha": 120,
        "ubicacion": {"latitud": -24.89, "longitud": -59.57},
        "suelo": {
            "tipo_suelo": "argiudol",
            "ph_suelo": 6.5,
            "materia_organica": 3.2,
            "materia_organica_pct": 3.2,
        },
        "clima": {
            "temp_media_marzo": 40.0,
            "temp_media_abril": 21.0,
            "temp_media_mayo": 13.0,
            "precipitacion_marzo": 120.0,
            "precipitacion_abril": 90.0,
            "precipitacion_mayo": 60.0,
        },
    },
    "c3f2f1ab-ca2e-4f8b-9819-377102c4d859": {
        "lote_id": "c3f2f1ab-ca2e-4f8b-9819-377102c4d859",
        "nombre": "Lote Pergamino Sur",
        "establecimiento_id": "est-123",
        "superficie_ha": 120,
        "ubicacion": {"latitud": -26.89, "longitud": -64.57},
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
}


class MainSystemAPIClient:
    """Cliente HTTP para comunicarse con el sistema agrícola principal."""

    def __init__(self, base_url: str, request: Optional[Request] = None):
        """Inicializa el cliente de la API principal.
        
        Args:
            base_url: URL base del sistema principal
            request: Request de FastAPI para extraer contexto de autenticación
        """
        self.base_url = base_url.rstrip("/")
        self._request = request
        self._timeout = 30.0

    @property
    def auth_token(self) -> Optional[str]:
        """Obtiene el token de autenticación del request actual.
        
        Returns:
            Token de autenticación si está disponible, None en caso contrario
        """
        if self._request and getattr(self._request.state, "user", None):
            return self._request.state.user.get("token")
        return None

    async def get_lote_data(self, lote_id: str) -> Dict:
        """Obtiene datos del lote desde el sistema principal.
        
        Args:
            lote_id: Identificador único del lote
            
        Returns:
            Diccionario con datos del lote (ubicación, suelo, clima)
            
        Raises:
            ValueError: Si el lote no existe
            httpx.HTTPError: Si hay error en la comunicación HTTP
        """
        url = f"{self.base_url}/api/lotes/{lote_id}"
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                lote_data = response.json()
                if not lote_data:
                    raise ValueError(f"Lote {lote_id} no encontrado")
                
                logger.info(
                    "Datos del lote obtenidos exitosamente",
                    extra={"lote_id": lote_id}
                )
                return lote_data
                
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ValueError(f"Lote {lote_id} no encontrado") from exc
                logger.error(
                    "Error HTTP al obtener datos del lote",
                    extra={
                        "lote_id": lote_id,
                        "status_code": exc.response.status_code,
                        "detail": str(exc)
                    }
                )
                raise
            except httpx.RequestError as exc:
                logger.error(
                    "Error de conexión al sistema principal",
                    extra={"lote_id": lote_id, "error": str(exc)}
                )
                raise