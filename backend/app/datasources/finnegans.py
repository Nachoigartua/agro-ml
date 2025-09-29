from typing import List, Optional
from app.datasources.base import DataSource, Campana, Lote, Cultivo, ClimateSummary

class FinAPISource(DataSource):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.api_key = api_key or ""

    # Estos métodos quedan listos para mapear endpoints reales de Finnegans.
    # Mientras no haya acceso al servicio, devolvemos listas vacías/None.
    # La capa superior mantiene la lógica de negocio sin hardcodear datos.
    def get_campanas(self) -> List[Campana]:
        return []

    def get_lotes(self) -> List[Lote]:
        return []

    def get_cultivos(self) -> List[Cultivo]:
        return []

    def climate_summary(self, lat: float, lon: float, dias: int) -> Optional[ClimateSummary]:
        return None

    def historic_yields(self, lote_id: str) -> List[int]:
        return []

    def soil_mo(self, lote_id: str) -> Optional[float]:
        return None
