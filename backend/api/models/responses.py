"""
Response models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PredictionResponse(BaseModel):
    """Response genérico para predicciones"""
    lote_id: Optional[str] = None
    tipo_prediccion: str = Field(..., description="Tipo de predicción realizada")
    recomendacion_principal: Dict[str, Any] = Field(..., description="Recomendación principal")
    alternativas: List[Dict[str, Any]] = Field(default=[], description="Alternativas")
    nivel_confianza: float = Field(..., description="Nivel de confianza (0-1)", ge=0, le=1)
    factores_considerados: List[str] = Field(..., description="Factores considerados")
    fecha_generacion: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class TrainResponse(BaseModel):
    """Response para entrenamiento de modelos"""
    modelo: str = Field(..., description="Nombre del modelo entrenado")
    status: str = Field(..., description="Estado del entrenamiento")
    metricas: Dict[str, float] = Field(..., description="Métricas de performance")
    fecha_entrenamiento: datetime = Field(default_factory=datetime.utcnow)
    mensaje: str = Field(..., description="Mensaje informativo")