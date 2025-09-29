from typing import Any, Dict, List, Optional
import httpx
from .provider import DataProvider

class HTTPDataProvider(DataProvider):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def get_lotes(self, cliente_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/lotes", params={"cliente_id": cliente_id})
            r.raise_for_status()
            return r.json()

    async def get_lote(self, lote_id: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/lotes/{lote_id}")
            r.raise_for_status()
            return r.json()

    async def get_ordenes_trabajo(self, lote_id: str, fecha_desde: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"lote_id": lote_id}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/ordenes-trabajo", params=params)
            r.raise_for_status()
            return r.json()

    async def get_cosechas_historicas(self, lote_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/cosechas", params={"lote_id": lote_id})
            r.raise_for_status()
            return r.json()

    async def validate_token(self, token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/auth/validate", headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                return {"valid": True, "user_info": r.json()}
            return {"valid": False}
