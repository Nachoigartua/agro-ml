from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DataProvider(ABC):
    """Puerto de datos: Finnegans solo reemplaza la implementación."""

    # ---- Lotes / Clientes ----
    @abstractmethod
    async def get_lotes(self, cliente_id: str) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def get_lote(self, lote_id: str) -> Optional[Dict[str, Any]]:
        ...

    # ---- Históricos ----
    @abstractmethod
    async def get_ordenes_trabajo(self, lote_id: str, fecha_desde: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def get_cosechas_historicas(self, lote_id: str) -> List[Dict[str, Any]]:
        ...

    # ---- Auth ----
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Devuelve info de usuario si es válido; lanza excepción o devuelve {'valid': False} si no."""
        ...
