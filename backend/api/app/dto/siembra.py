from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

ALLOWED_CULTIVOS = {"trigo", "soja", "maiz", "cebada"}


class RecomendacionResponse(BaseModel):
    """Respuesta base para cualquier tipo de recomendación."""

    lote_id: str
    tipo_recomendacion: str
    recomendacion_principal: Dict[str, Any]
    alternativas: List[Dict[str, Any]] = Field(default_factory=list)
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    factores_considerados: List[str] = Field(default_factory=list)
    costos_estimados: Dict[str, float] = Field(default_factory=dict)
    fecha_generacion: datetime
    datos_entrada: Dict[str, Any] = Field(default_factory=dict)


class RecomendacionPrincipalSiembra(BaseModel):
    """Estructura de la recomendación principal para siembra."""

    fecha_optima: str
    ventana: List[str]
    confianza: float = Field(ge=0.0, le=1.0)
    
    # Lista de riesgos, se inicia vacía para evitar referencias compartidas.
    riesgos: List[str] = Field(default_factory=list)


class SiembraRequest(BaseModel):

    lote_id: str
    cultivo: str
    campana: str
    fecha_consulta: datetime
    cliente_id: str

    @field_validator("cultivo")
    @classmethod
    def validate_cultivo(cls, value: str) -> str:
        normalised = value.lower()
        if normalised not in ALLOWED_CULTIVOS:
            allowed = ", ".join(sorted(ALLOWED_CULTIVOS))
            raise ValueError(f"cultivo debe ser uno de: {allowed}")
        return normalised


class SiembraRecommendationResponse(RecomendacionResponse):
    """Respuesta de recomendación de siembra.

    Extiende la respuesta base agregando el cultivo como metadato de alto nivel.
    """

    cultivo: str
    recomendacion_principal: RecomendacionPrincipalSiembra


class SiembraHistoryItem(BaseModel):
    """Elemento del historial de recomendaciones de siembra."""

    id: UUID
    lote_id: UUID
    cliente_id: UUID
    cultivo: Optional[str] = None
    campana: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_validez_desde: Optional[date] = None
    fecha_validez_hasta: Optional[date] = None
    nivel_confianza: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    recomendacion_principal: RecomendacionPrincipalSiembra
    alternativas: List[Dict[str, Any]] = Field(default_factory=list)
    modelo_version: Optional[str] = None
    datos_entrada: Dict[str, Any] = Field(default_factory=dict)


class SiembraHistoryResponse(BaseModel):
    """Respuesta para el endpoint de historial de siembra."""

    total: int
    items: List[SiembraHistoryItem]
