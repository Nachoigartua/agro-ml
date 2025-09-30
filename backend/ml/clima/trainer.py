"""
Trainer para el modelo climático
"""
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class ClimaTrainer:
    """Entrenador del modelo climático"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo climático...")
        
        # Para clima usamos un modelo simple de series temporales
        # En producción se usaría ARIMA o LSTM
        
        X, y = self._generate_training_data()
        
        self.preprocessor = StandardScaler()
        X_scaled = self.preprocessor.fit_transform(X)
        
        logger.info("Entrenando modelo de series temporales...")
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)
        
        metrics = {
            "model_type": "linear_regression",
            "n_samples": len(X),
            "features": ["historical_mean", "seasonal_component", "trend"]
        }
        
        logger.info("Modelo climático entrenado")
        
        return metrics
    
    def _generate_training_data(self, n_samples: int = 365) -> tuple:
        """Genera datos sintéticos de series temporales"""
        
        np.random.seed(42)
        
        # Simular serie temporal de temperatura
        days = np.arange(n_samples)
        
        # Componente estacional
        seasonal = 10 * np.sin(2 * np.pi * days / 365)
        
        # Tendencia
        trend = 0.01 * days
        
        # Promedio histórico
        historical_mean = np.ones(n_samples) * 18
        
        X = pd.DataFrame({
            "historical_mean": historical_mean,
            "seasonal_component": seasonal,
            "trend": trend
        })
        
        # Target: temperatura real
        y = historical_mean + seasonal + trend + np.random.normal(0, 2, n_samples)
        
        return X, y