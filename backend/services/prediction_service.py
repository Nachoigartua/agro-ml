"""
Main prediction service that orchestrates ML models
"""
from typing import Dict, Any
from datetime import datetime
from ml.siembra.model import SiembraModel
from ml.variedades.model import VariedadesModel
from ml.rendimiento.model import RendimientoModel
from ml.fertilizacion.model import FertilizacionModel
from ml.clima.model import ClimaModel
from ml.cosecha.model import CosechaModel
from services.cache_service import cache_service
from database.repositories import PredictionRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class PredictionService:
    """Service to handle all ML predictions"""
    
    def __init__(self):
        self.models = {
            "siembra": SiembraModel(),
            "variedades": VariedadesModel(),
            "rendimiento": RendimientoModel(),
            "fertilizacion": FertilizacionModel(),
            "clima": ClimaModel(),
            "cosecha": CosechaModel()
        }
        self.repository = PredictionRepository()
    
    async def initialize(self):
        """Initialize all models (load from disk if available)"""
        logger.info("Inicializando modelos ML...")
        
        for name, model in self.models.items():
            try:
                if model.load_model():
                    logger.info(f"Modelo {name} cargado exitosamente")
                else:
                    logger.warning(f"Modelo {name} no encontrado, será entrenado en primera predicción")
            except Exception as e:
                logger.error(f"Error cargando modelo {name}: {e}")
        
        # Connect cache
        await cache_service.connect()
        
        logger.info("Modelos ML inicializados")
    
    async def predict_siembra(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate siembra prediction"""
        return await self._predict_with_cache("siembra", data)
    
    async def predict_variedades(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate variedades prediction"""
        return await self._predict_with_cache("variedades", data)
    
    async def predict_rendimiento(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rendimiento prediction"""
        return await self._predict_with_cache("rendimiento", data)
    
    async def predict_fertilizacion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fertilizacion prediction"""
        return await self._predict_with_cache("fertilizacion", data)
    
    async def predict_clima(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clima prediction"""
        return await self._predict_with_cache("clima", data)
    
    async def predict_cosecha(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cosecha prediction"""
        return await self._predict_with_cache("cosecha", data)
    
    async def _predict_with_cache(
        self, 
        prediction_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make prediction with caching"""
        
        # Generate cache key
        cache_key = cache_service.generate_cache_key(prediction_type, data)
        
        # Try to get from cache
        cached_result = await cache_service.get_cached_prediction(cache_key)
        if cached_result:
            logger.info(f"Returning cached {prediction_type} prediction")
            return cached_result
        
        # Make prediction
        logger.info(f"Generating new {prediction_type} prediction")
        model = self.models.get(prediction_type)
        if not model:
            raise ValueError(f"Unknown prediction type: {prediction_type}")
        
        result = await model.predict(data)
        
        # Cache result
        await cache_service.cache_prediction(cache_key, result)
        
        # Save to database
        try:
            await self.repository.save_prediction(result)
        except Exception as e:
            logger.error(f"Error guardando predicción en BD: {e}")
        
        return result
    
    async def train_model(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Train or retrain a model"""
        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Unknown model: {model_name}")
        
        logger.info(f"Iniciando entrenamiento de modelo {model_name}")
        
        result = await model.train(data)
        
        # Invalidate cache for this model
        await cache_service.invalidate_cache(f"prediction:{model_name}:*")
        
        return {
            "modelo": model_name,
            "status": result.get("status", "success"),
            "metricas": result.get("metrics", {}),
            "fecha_entrenamiento": datetime.utcnow(),
            "mensaje": f"Modelo {model_name} entrenado exitosamente"
        }
    
    async def get_models_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}
        
        for name, model in self.models.items():
            status[name] = model.get_model_info()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "models": status,
            "cache_connected": await cache_service.ping()
        }


# Global prediction service instance
prediction_service = PredictionService()