from typing import List, Optional
from pydantic import BaseModel, validator
import uuid
from datetime import date

ALLOWED_CULTIVOS = ["trigo", "soja", "maiz", "cebada"]

class SiembraRequest(BaseModel):
    lote_id: str
    cliente_id: str
    cultivo: str

    @validator("cultivo")
    def _val_cultivo(cls, v: str):
        if v.lower() not in ALLOWED_CULTIVOS:
            raise ValueError(f"cultivo debe ser uno de: {ALLOWED_CULTIVOS}")
        return v.lower()

    @validator("lote_id")
    def _val_uuid(cls, v: str):
        uuid.UUID(v)  # lanzará ValueError si es inválido
        return v

class Recomendacion(BaseModel):
    recomendacion_principal: str
    fecha_optima: Optional[date]
    ventana_inicio: Optional[date]
    ventana_fin: Optional[date]
    confianza: float
    riesgos: Optional[str]
    alternativas: List[str] = []

class LoteDTO(BaseModel):
    id: str
    cliente_id: str
    nombre: Optional[str]
    superficie_ha: Optional[float]
    geom_wkt: Optional[str]
