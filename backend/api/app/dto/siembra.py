from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_CULTIVOS = {"trigo", "soja", "maiz", "cebada"}


class SiembraRecommendationDetail(BaseModel):
    """Detalle de la recomendación de siembra."""

    cultivo: str
    fecha_siembra: datetime


class SiembraRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lote_id: str
    cliente_id: str
    cultivo: str
    campana: str
    fecha_consulta: datetime

    @field_validator("lote_id", "cliente_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("identificador no puede estar vacio")
        return value

    @field_validator("cultivo")
    @classmethod
    def validate_cultivo(cls, value: str) -> str:
        normalised = value.lower()
        if normalised not in ALLOWED_CULTIVOS:
            allowed = ", ".join(sorted(ALLOWED_CULTIVOS))
            raise ValueError(f"cultivo debe ser uno de: {allowed}")
        return normalised


class SiembraRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lote_id: str
    tipo_recomendacion: Literal["siembra"] = Field(default="siembra")
    recomendacion_principal: SiembraRecommendationDetail
