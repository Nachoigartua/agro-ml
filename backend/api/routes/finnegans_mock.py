"""
Mock endpoints that simulate Finnegans API
Solo disponible cuando USE_MOCK_DATA=true
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.data_mock_service import DataMockService

router = APIRouter()
mock_service = DataMockService()


@router.get("/lotes")
async def get_lotes(cliente_id: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene datos de lotes (simula endpoint de Finnegans)
    """
    lotes = mock_service.get_mock_lotes_data()
    
    if cliente_id:
        lotes = [l for l in lotes if l.get("cliente_id") == cliente_id]
    
    return lotes


@router.get("/lotes/{lote_id}")
async def get_lote(lote_id: str) -> Dict[str, Any]:
    """
    Obtiene datos de un lote específico
    """
    lotes = mock_service.get_mock_lotes_data()
    lote = next((l for l in lotes if l.get("id") == lote_id), None)
    
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    return lote


@router.get("/ordenes-trabajo")
async def get_ordenes_trabajo(lote_id: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene órdenes de trabajo (simula endpoint de Finnegans)
    """
    ordenes = mock_service.get_mock_ordenes_trabajo()
    
    if lote_id:
        ordenes = [o for o in ordenes if o.get("lote_id") == lote_id]
    
    return ordenes


@router.get("/cosechas")
async def get_cosechas(lote_id: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene datos de cosechas históricas
    """
    cosechas = mock_service.get_mock_cosechas_historicas()
    
    if lote_id:
        cosechas = [c for c in cosechas if c.get("lote_id") == lote_id]
    
    return cosechas


@router.get("/clima")
async def get_clima_historico(latitud: float, longitud: float) -> List[Dict[str, Any]]:
    """
    Obtiene datos climáticos históricos
    """
    return mock_service.get_mock_clima_data(latitud, longitud)


@router.get("/suelo/{lote_id}")
async def get_caracteristicas_suelo(lote_id: str) -> Dict[str, Any]:
    """
    Obtiene características del suelo de un lote
    """
    return mock_service.get_mock_suelo_data(lote_id)