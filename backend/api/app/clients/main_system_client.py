"""Cliente para la API del sistema principal."""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import Depends, Request

from ..core.logging import get_logger


logger = get_logger("main_system_client")


class MainSystemAPIClient:
    """Cliente para interactuar con la API del sistema principal."""
    
    def __init__(self, base_url: str, request: Optional[Request] = None):
        self.base_url = base_url
        self._request = request
        
    @property
    def auth_token(self) -> Optional[str]:
        """Obtiene el token de autenticación del request actual."""
        if self._request and self._request.state.user:
            return self._request.state.user.get("token")
        return None
        
    async def get_lote_data(self, lote_id: str) -> Dict:
        """Obtiene datos del lote desde el sistema principal."""
        #TODO: Implementar la llamada real a la API del sistema principal
        return
        
