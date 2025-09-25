from pydantic import BaseModel
from typing import Optional, List

class Coord(BaseModel):
    latitud: float; longitud: float
class SiembraRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
    coords: Coord
    tipo_suelo: Optional[str] = None
    fecha_referencia: Optional[str] = None
class VariedadRequest(BaseModel):
    cultivo: str
    zona: Optional[str] = None
    objetivos: Optional[List[str]] = None
class ClimaRequest(BaseModel):
    coords: Coord
    periodo: str
class FertilizacionRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
    objetivo: Optional[str] = None
class AgroquimicosRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
class RendimientoRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
    manejo_previsto: Optional[List[str]] = None
class CosechaRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
class AplicarRequest(BaseModel):
    lote_id: Optional[str] = None
    cultivo: str
    seleccion: dict
