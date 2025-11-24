from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_CULTIVOS = {"trigo", "soja", "maiz", "cebada"}


class RecomendacionResponse(BaseModel):
    """Respuesta base para cualquier tipo de recomendación."""

    lote_id: str
    tipo_recomendacion: str
    prediccion_id: Optional[UUID] = None
    recomendacion_principal: Dict[str, Any]
    alternativas: List[Dict[str, Any]] = Field(default_factory=list)
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    costos_estimados: Dict[str, float] = Field(default_factory=dict)
    fecha_generacion: datetime
    datos_entrada: Dict[str, Any] = Field(default_factory=dict)


class RecomendacionPrincipalSiembra(BaseModel):
    """Estructura de la recomendación principal para siembra.
    
    Combina validaciones de REFACTOR (ventana length) con
    feature de análisis de riesgo de DEV (campo riesgos).
    """

    fecha_optima: str
    ventana: List[str] = Field(min_length=2, max_length=2)  # De REFACTOR
    confianza: float = Field(ge=0.0, le=1.0)
    riesgos: List[str] = Field(default_factory=list)  # De DEV - Análisis de riesgo


class SiembraRequest(BaseModel):
    """Request para generar recomendación de siembra."""

    lote_id: str
    cultivo: str
    campana: str
    fecha_consulta: datetime
    cliente_id: str

    @field_validator("cultivo")
    @classmethod
    def validate_cultivo(cls, value: str) -> str:
        """Valida que el cultivo sea uno de los permitidos."""
        normalised = value.lower()
        if normalised not in ALLOWED_CULTIVOS:
            allowed = ", ".join(sorted(ALLOWED_CULTIVOS))
            raise ValueError(f"cultivo debe ser uno de: {allowed}")
        return normalised


class BulkSiembraRequest(BaseModel):
    """Request envoltorio para generar recomendaciones de múltiples lotes."""

    lote_ids: List[str] = Field(min_length=1)
    cultivo: str
    campana: str
    fecha_consulta: datetime
    cliente_id: str

    @field_validator("lote_ids")
    @classmethod
    def validate_lote_ids(cls, value: List[str]) -> List[str]:
        """Garantiza que la lista tenga elementos únicos."""
        seen = set()
        duplicates = set()
        for lote_id in value:
            if lote_id in seen:
                duplicates.add(lote_id)
            seen.add(lote_id)

        if duplicates:
            duplicated = ", ".join(sorted(duplicates))
            raise ValueError(f"lote_ids contiene duplicados: {duplicated}")
        return value

    @field_validator("cultivo")
    @classmethod
    def validate_cultivo(cls, value: str) -> str:
        """Reutiliza las reglas del request individual."""
        return SiembraRequest.validate_cultivo(value)


class SiembraRecommendationResponse(RecomendacionResponse):
    """Respuesta de recomendación de siembra.

    Extiende la respuesta base agregando el cultivo como metadato de alto nivel.
    """

    cultivo: str
    recomendacion_principal: RecomendacionPrincipalSiembra


class BulkSiembraRecommendationItem(BaseModel):
    """Elemento individual del resultado bulk.

    Contiene la respuesta completa si la generación fue exitosa, o el detalle de error.
    """

    lote_id: str
    success: bool
    response: Optional[SiembraRecommendationResponse] = None
    error: Optional[str] = None

    @model_validator(mode="after")
    def validate_payload(self) -> BulkSiembraRecommendationItem:
        """Asegura consistencia entre flags y datos adjuntos."""
        if self.success and self.response is None:
            raise ValueError("response debe estar presente cuando success es True")
        if not self.success and not self.error:
            raise ValueError("error debe estar presente cuando success es False")
        return self


class BulkSiembraResponse(BaseModel):
    """Respuesta agrupada para recomendaciones de múltiples lotes."""

    total: int
    resultados: List[BulkSiembraRecommendationItem]


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

class RecommendationPdfRequest(BaseModel):
    """Payload para generar un PDF de recomendación."""

    recomendacion: SiembraRecommendationResponse
    metadata: Dict[str, Any] = Field(default_factory=dict)
