from typing import List, Optional, Protocol
from pydantic import BaseModel

class Coordinates(BaseModel):
    latitud: float
    longitud: float

class ClimateSummary(BaseModel):
    temp_media: float
    precip: float
    humedad: float
    viento: float
    radiacion: float

class Lote(BaseModel):
    id: str
    nombre: str
    latitud: float
    longitud: float
    hectareas: float
    cultivo_id: Optional[str] = None

class Campana(BaseModel):
    id: str
    nombre: str

class Cultivo(BaseModel):
    id: str
    nombre: str
    tipo: Optional[str] = None

class DataSource(Protocol):
    def get_campanas(self) -> List[Campana]: ...
    def get_lotes(self) -> List[Lote]: ...
    def get_cultivos(self) -> List[Cultivo]: ...

    def climate_summary(self, lat: float, lon: float, dias: int) -> Optional[ClimateSummary]: ...
    def historic_yields(self, lote_id: str) -> List[int]: ...
    def soil_mo(self, lote_id: str) -> Optional[float]: ...
