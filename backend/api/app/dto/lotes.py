from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class LoteItem(BaseModel):
    """Representa un lote para visualización en mapa."""

    lote_id: str
    nombre: str = Field(default_factory=str)
    latitud: float
    longitud: float


class LotesListResponse(BaseModel):
    """Respuesta para listar lotes."""

    total: int
    items: List[LoteItem]

