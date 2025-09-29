from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, conlist

class Lote(BaseModel):
    id: str
    nombre: str
    latitud: float
    longitud: float

class Campana(BaseModel):
    nombre: str

class Cultivo(BaseModel):
    nombre: str

class ClimaRequest(BaseModel):
    latitud: float
    longitud: float

class ClimaResponse(BaseModel):
    temp_media: float
    precip: float
    humedad: float
    viento: float
    radiacion: float

class SiembraRequest(BaseModel):
    lote_id: str
    cultivo: str
    campana: str
    objetivo: Optional[str] = None

class SiembraRecomendacion(BaseModel):
    fecha_recomendada: date
    densidad_semillas_kg_ha: float
    distancia_entre_hileras_cm: float
    observaciones: Optional[str] = None

class VariedadesRequest(BaseModel):
    cultivo: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    campana: Optional[str] = None

class Variedad(BaseModel):
    nombre: str
    madurez: str
    rendimiento_base_kg_ha: float
    tolerancias: Dict[str, str] = Field(default_factory=dict)
    justificacion: str

class RendimientoRequest(BaseModel):
    lote_id: str
    cultivo: str
    campana: str

class RendimientoResponse(BaseModel):
    rendimiento_estimado_kg_ha: float
    intervalo_confianza_kg_ha: conlist(float, min_items=2, max_items=2)
    factores: Dict[str, float]

class FertilizacionRequest(BaseModel):
    lote_id: str
    cultivo: str
    campana: str
    rendimiento_objetivo_kg_ha: Optional[float] = None

class FertilizacionResponse(BaseModel):
    dosis_N_kg_ha: float
    dosis_P2O5_kg_ha: float
    dosis_K2O_kg_ha: float
    costo_estimado_usd_ha: float
    detalle: Dict[str, Any]

class CosechaRequest(BaseModel):
    cultivo: str
    fecha_siembra: date
    campana: str

class CosechaResponse(BaseModel):
    fecha_optima: date
    dias_restantes: int
