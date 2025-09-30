"""
Base class for ML models
"""
from abc import ABC, abstractmethod
import joblib
import os
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class BaseMLModel(ABC):
    """Base class for all ML models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.preprocessor = None
        self.metadata = {
            "trained_at": None,
            "version": "1.0.0",
            "metrics": {}
        }
        self.model_path = Path(settings.ML_MODELS_PATH) / f"{model_name}.joblib"
    
    @abstractmethod
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Train the model with provided data"""
        pass
    
    @abstractmethod
    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a prediction with the model"""
        pass
    
    def save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                "model": self.model,
                "preprocessor": self.preprocessor,
                "metadata": self.metadata
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"Modelo {self.model_name} guardado en {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error guardando modelo {self.model_name}: {e}")
            raise
    
    def load_model(self) -> bool:
        """Load model from disk"""
        try:
            if not self.model_path.exists():
                logger.warning(f"No se encontró modelo en {self.model_path}")
                return False
            
            model_data = joblib.load(self.model_path)
            self.model = model_data.get("model")
            self.preprocessor = model_data.get("preprocessor")
            self.metadata = model_data.get("metadata", {})
            
            logger.info(f"Modelo {self.model_name} cargado desde {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando modelo {self.model_name}: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "name": self.model_name,
            "loaded": self.model is not None,
            "metadata": self.metadata,
            "path": str(self.model_path)
        }