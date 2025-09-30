"""
ML API Routes for predictions and training
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.models.requests import (
    SiembraRequest,
    VariedadRequest,
    RendimientoRequest,
    FertilizacionRequest,
    ClimaRequest,
    CosechaRequest,
    TrainModelRequest
)
from api.models.responses import PredictionResponse, TrainResponse
from api.middleware.auth import verify_api_key
from services.prediction_service import prediction_service
from utils.logger import get_logger
from config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post("/predict/siembra", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_siembra(
    request: Request,
    data: SiembraRequest,
    api_key: str = Depends(verify_api_key)
):
    """Genera recomendaciones de fechas óptimas de siembra"""
    try:
        logger.info(f"Predicción de siembra solicitada para lote {data.lote_id}")
        result = await prediction_service.predict_siembra(data)
        logger.info(f"Predicción de siembra completada para lote {data.lote_id}")
        return result
    except Exception as e:
        logger.error(f"Error en predicción de siembra: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/variedades", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_variedades(
    request: Request,
    data: VariedadRequest,
    api_key: str = Depends(verify_api_key)
):
    """Recomienda variedades de semillas por lote"""
    try:
        logger.info(f"Predicción de variedades solicitada para lote {data.lote_id}")
        result = await prediction_service.predict_variedades(data)
        logger.info(f"Predicción de variedades completada para lote {data.lote_id}")
        return result
    except Exception as e:
        logger.error(f"Error en predicción de variedades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/rendimiento", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_rendimiento(
    request: Request,
    data: RendimientoRequest,
    api_key: str = Depends(verify_api_key)
):
    """Predice rendimientos esperados por lote y cultivo"""
    try:
        logger.info(f"Predicción de rendimiento solicitada para lote {data.lote_id}")
        result = await prediction_service.predict_rendimiento(data)
        logger.info(f"Predicción de rendimiento completada para lote {data.lote_id}")
        return result
    except Exception as e:
        logger.error(f"Error en predicción de rendimiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/fertilizacion", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_fertilizacion(
    request: Request,
    data: FertilizacionRequest,
    api_key: str = Depends(verify_api_key)
):
    """Genera plan de fertilización optimizado"""
    try:
        logger.info(f"Predicción de fertilización solicitada para lote {data.lote_id}")
        result = await prediction_service.predict_fertilizacion(data)
        logger.info(f"Predicción de fertilización completada para lote {data.lote_id}")
        return result
    except Exception as e:
        logger.error(f"Error en predicción de fertilización: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/clima", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_clima(
    request: Request,
    data: ClimaRequest,
    api_key: str = Depends(verify_api_key)
):
    """Proporciona predicciones climáticas"""
    try:
        logger.info(f"Predicción climática solicitada para coordenadas {data.latitud}, {data.longitud}")
        result = await prediction_service.predict_clima(data)
        logger.info("Predicción climática completada")
        return result
    except Exception as e:
        logger.error(f"Error en predicción climática: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/cosecha", response_model=PredictionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def predict_cosecha(
    request: Request,
    data: CosechaRequest,
    api_key: str = Depends(verify_api_key)
):
    """Determina momentos óptimos de cosecha"""
    try:
        logger.info(f"Predicción de cosecha solicitada para lote {data.lote_id}")
        result = await prediction_service.predict_cosecha(data)
        logger.info(f"Predicción de cosecha completada para lote {data.lote_id}")
        return result
    except Exception as e:
        logger.error(f"Error en predicción de cosecha: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/{modelo}", response_model=TrainResponse)
async def train_model(
    modelo: str,
    data: TrainModelRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Entrena o reentrena un modelo específico
    
    Modelos disponibles: siembra, variedades, rendimiento, fertilizacion, clima, cosecha
    """
    try:
        logger.info(f"Entrenamiento de modelo '{modelo}' solicitado")
        
        valid_models = ["siembra", "variedades", "rendimiento", "fertilizacion", "clima", "cosecha"]
        if modelo not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Modelo '{modelo}' no válido. Modelos disponibles: {', '.join(valid_models)}"
            )
        
        result = await prediction_service.train_model(modelo, data.dict())
        logger.info(f"Entrenamiento de modelo '{modelo}' completado")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en entrenamiento de modelo '{modelo}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_models_status(api_key: str = Depends(verify_api_key)):
    """Obtiene el estado de todos los modelos ML"""
    try:
        status = await prediction_service.get_models_status()
        return status
    except Exception as e:
        logger.error(f"Error obteniendo estado de modelos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))