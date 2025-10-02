﻿from __future__ import annotations

import re
from datetime import date, datetime
from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_CULTIVOS = {"trigo", "soja", "maiz", "cebada"}

class RecomendacionBase(BaseModel):
    """Modelo base para recomendaciones."""
    cultivo: str
    fecha_siembra: datetime
    densidad_siembra: float
    profundidad_siembra: float
    espaciamiento_hileras: float
    score: float = Field(ge=0.0, le=1.0)

class SiembraRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lote_id: UUID
    cliente_id: UUID
    cultivo: str
    campana: str
    fecha_consulta: datetime

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

    lote_id: UUID
    tipo_recomendacion: str = Field(default="siembra")
    recomendacion_principal: RecomendacionBase
    alternativas: List[RecomendacionBase]
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    factores_considerados: List[str]
    costos_estimados: Dict[str, float]
    fecha_generacion: datetime
