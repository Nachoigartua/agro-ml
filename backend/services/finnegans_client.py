"""
Client for Finnegans API (or mock data)
"""
import httpx
from typing import Dict, Any, List, Optional
from config import settings
from utils.logger import get_logger
from services.data_mock_service import DataMockService

logger = get_logger(__name__)


class FinnegansClient:
    """Client to interact with Finnegans API or mock data"""
    
    def __init__(self):
        self.base_url = settings.FINNEGANS_API_URL
        self.api_key = settings.FINNEGANS_API_KEY
        self.use_mock = settings.USE_MOCK_DATA
        self.mock_service = DataMockService() if self.use_mock else None
        self.timeout = 30.0
    
    async def get_lote_data(self, lote_id: str) -> Dict[str, Any]:
        """Get lote data from Finnegans API or mock"""
        if self.use_mock:
            return self.mock_service.get_mock_lote_by_id(lote_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/lotes/{lote_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo datos de lote {lote_id}: {e}")
            raise
    
    async def get_lotes_by_cliente(self, cliente_id: str) -> List[Dict[str, Any]]:
        """Get all lotes for a cliente"""
        if self.use_mock:
            return self.mock_service.get_mock_lotes_by_cliente(cliente_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/lotes",
                    params={"cliente_id": cliente_id},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo lotes del cliente {cliente_id}: {e}")
            raise
    
    async def get_ordenes_trabajo(
        self, 
        lote_id: str, 
        fecha_desde: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get ordenes de trabajo for a lote"""
        if self.use_mock:
            return self.mock_service.get_mock_ordenes_trabajo(lote_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"lote_id": lote_id}
                if fecha_desde:
                    params["fecha_desde"] = fecha_desde
                
                response = await client.get(
                    f"{self.base_url}/api/ordenes-trabajo",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo órdenes de trabajo: {e}")
            raise
    
    async def get_cosechas_historicas(self, lote_id: str) -> List[Dict[str, Any]]:
        """Get historical harvest data for a lote"""
        if self.use_mock:
            return self.mock_service.get_mock_cosechas_historicas(lote_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/cosechas",
                    params={"lote_id": lote_id},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo cosechas históricas: {e}")
            raise
    
    async def get_clima_historico(
        self, 
        latitud: float, 
        longitud: float,
        dias: int = 365
    ) -> List[Dict[str, Any]]:
        """Get historical climate data"""
        if self.use_mock:
            return self.mock_service.get_mock_clima_data(latitud, longitud, dias)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/clima",
                    params={
                        "latitud": latitud,
                        "longitud": longitud,
                        "dias": dias
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo clima histórico: {e}")
            raise
    
    async def get_caracteristicas_suelo(self, lote_id: str) -> Dict[str, Any]:
        """Get soil characteristics for a lote"""
        if self.use_mock:
            return self.mock_service.get_mock_suelo_data(lote_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/suelo/{lote_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo características de suelo: {e}")
            raise


# Global Finnegans client instance
finnegans_client = FinnegansClient()