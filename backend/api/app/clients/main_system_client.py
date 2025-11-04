"""Cliente para la API del sistema principal."""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import Request
import httpx

from ..core.logging import get_logger


logger = get_logger("main_system_client")


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