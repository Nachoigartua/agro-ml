"""
Trainer para el modelo de rendimiento
"""
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class RendimientoTrainer:
    """Entrenador del modelo de rendimiento"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo de rendimiento...")
        
        X, y = self._generate_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.preprocessor = StandardScaler()
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        logger.info("Entrenando Gradient Boosting Regressor...")
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            "rmse_kg_ha": float(rmse),
            "mae_kg_ha": float(mae),
            "r2_score": float(r2),
            "n_samples": len(X)
        }
        
        logger.info(f"Modelo entrenado - RMSE: {rmse:.0f} kg/ha, R²: {r2:.3f}")
        
        return metrics
    
    def _generate_training_data(self, n_samples: int = 1000) -> tuple:
        """Genera datos sintéticos para entrenamiento"""
        
        np.random.seed(42)
        
        data = {
            "cultivo_encoded": np.random.randint(0, 5, n_samples),
            "temp_media_ciclo": np.random.uniform(12, 24, n_samples),
            "precipitacion_ciclo": np.random.uniform(200, 600, n_samples),
            "ph_suelo": np.random.uniform(5.5, 7.5, n_samples),
            "materia_organica": np.random.uniform(1.5, 5, n_samples),
            "nitrogeno": np.random.uniform(10, 40, n_samples),
            "fosforo": np.random.uniform(8, 30, n_samples),
            "potasio": np.random.uniform(100, 300, n_samples),
            "rendimiento_historico": np.random.uniform(2000, 5000, n_samples),
            "superficie_ha": np.random.uniform(50, 300, n_samples)
        }
        
        X = pd.DataFrame(data)
        
        # Target: rendimiento en kg/ha
        # Modelo simplificado: rendimiento base + efectos de clima, suelo y manejo
        y = (
            2000 +  # Rendimiento base
            (X["temp_media_ciclo"] - 18) * 50 +  # Efecto temperatura
            (X["precipitacion_ciclo"] - 400) * 2 +  # Efecto precipitación
            X["materia_organica"] * 200 +  # Efecto MO
            X["nitrogeno"] * 30 +  # Efecto N
            (X["rendimiento_historico"] - 3000) * 0.3 +  # Efecto histórico
            np.random.normal(0, 300, n_samples)  # Ruido
        )
        
        # Limitar valores razonables
        y = np.clip(y, 1000, 8000)
        
        return X, y