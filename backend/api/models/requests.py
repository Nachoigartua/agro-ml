"""
Request models for API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime


class SiembraRequest(BaseModel):
    """Request para predicción de siembra"""
    lote_id: str = Field(..., description="ID del lote")
    cliente_id: str = Field(..., description="ID del cliente")
    cultivo: str = Field(..., description="Tipo de cultivo")
    campana: str = Field(..., description="Campaña agrícola (ej: 2024/2025)")
    
    @validator('cultivo')
    def validate_cultivo(cls, v):
        allowed_cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol']
        if v.lower() not in allowed_cultivos:
            raise ValueError(f'Cultivo debe ser uno de: {", ".join(allowed_cultivos)}')
        return v.lower()


class VariedadRequest(BaseModel):
    """Request para recomendación de variedades"""
    lote_id: str = Field(..., description="ID del lote")
    cliente_id: str = Field(..., description="ID del cliente")
    cultivo: str = Field(..., description="Tipo de cultivo")
    objetivo_productivo: Optional[str] = Field(None, description="Objetivo productivo")
    
    @validator('cultivo')
    def validate_cultivo(cls, v):
        allowed_cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol']
        if v.lower() not in allowed_cultivos:
            raise ValueError(f'Cultivo debe ser uno de: {", ".join(allowed_cultivos)}')
        return v.lower()


class RendimientoRequest(BaseModel):
    """Request para predicción de rendimiento"""
    lote_id: str = Field(..., description="ID del lote")
    cliente_id: str = Field(..., description="ID del cliente")
    cultivo: str = Field(..., description="Tipo de cultivo")
    fecha_siembra: date = Field(..., description="Fecha de siembra")
    variedad: Optional[str] = Field(None, description="Variedad de semilla")
    
    @validator('cultivo')
    def validate_cultivo(cls, v):
        allowed_cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol']
        if v.lower() not in allowed_cultivos:
            raise ValueError(f'Cultivo debe ser uno de: {", ".join(allowed_cultivos)}')
        return v.lower()


class FertilizacionRequest(BaseModel):
    """Request para recomendación de fertilización"""
    lote_id: str = Field(..., description="ID del lote")
    cliente_id: str = Field(..., description="ID del cliente")
    cultivo: str = Field(..., description="Tipo de cultivo")
    objetivo_rendimiento: Optional[float] = Field(None, description="Objetivo de rendimiento en kg/ha")
    
    @validator('cultivo')
    def validate_cultivo(cls, v):
        allowed_cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol']
        if v.lower() not in allowed_cultivos:
            raise ValueError(f'Cultivo debe ser uno de: {", ".join(allowed_cultivos)}')
        return v.lower()


class ClimaRequest(BaseModel):
    """Request para predicción climática"""
    latitud: float = Field(..., description="Latitud", ge=-90, le=90)
    longitud: float = Field(..., description="Longitud", ge=-180, le=180)
    fecha_desde: date = Field(..., description="Fecha desde")
    fecha_hasta: date = Field(..., description="Fecha hasta")
    
    @validator('fecha_hasta')
    def validate_fechas(cls, v, values):
        if 'fecha_desde' in values and v < values['fecha_desde']:
            raise ValueError('fecha_hasta debe ser posterior a fecha_desde')
        return v


class CosechaRequest(BaseModel):
    """Request para recomendación de cosecha"""
    lote_id: str = Field(..., description="ID del lote")
    cliente_id: str = Field(..., description="ID del cliente")
    cultivo: str = Field(..., description="Tipo de cultivo")
    fecha_siembra: date = Field(..., description="Fecha de siembra")
    variedad: Optional[str] = Field(None, description="Variedad de semilla")
    
    @validator('cultivo')
    def validate_cultivo(cls, v):
        allowed_cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol']
        if v.lower() not in allowed_cultivos:
            raise ValueError(f'Cultivo debe ser uno de: {", ".join(allowed_cultivos)}')
        return v.lower()


class TrainModelRequest(BaseModel):
    """Request para entrenar un modelo"""
    force_retrain: bool = Field(default=False, description="Forzar reentrenamiento")