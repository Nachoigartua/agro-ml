"""
Trainer para el modelo de cosecha
"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class CosechaTrainer:
    """Entrenador del modelo de cosecha"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo de cosecha...")
        
        X, y = self._generate_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.preprocessor = StandardScaler()
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        logger.info("Entrenando Random Forest Regressor...")
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            "mae_days": float(mae),
            "r2_score": float(r2),
            "n_samples": len(X)
        }
        
        logger.info(f"Modelo entrenado - MAE: {mae:.2f} días, R²: {r2:.3f}")
        
        return metrics
    
    def _generate_training_data(self, n_samples: int = 1000) -> tuple:
        """Genera datos sintéticos para entrenamiento"""
        
        np.random.seed(42)
        
        data = {
            "cultivo_encoded": np.random.randint(0, 5, n_samples),
            "dias_desde_siembra": np.random.uniform(80, 150, n_samples),
            "grados_dia_acumulados": np.random.uniform(800, 2000, n_samples),
            "temp_media_reciente": np.random.uniform(12, 26, n_samples),
            "precipitacion_reciente": np.random.uniform(0, 50, n_samples),
            "ciclo_variedad_encoded": np.random.randint(0, 3, n_samples)
        }
        
        X = pd.DataFrame(data)
        
        # Target: días hasta cosecha óptima
        # Base por cultivo
        dias_base = 120
        
        # Ajustar por madurez actual
        madurez = X["grados_dia_acumulados"] / 1500  # Factor de madurez
        
        y = (
            dias_base - X["dias_desde_siembra"] +
            (1 - madurez) * 30 +  # Menos días si más maduro
            X["ciclo_variedad_encoded"] * 10 +  # Ciclo largo suma días
            np.random.normal(0, 5, n_samples)
        )
        
        # Limitar entre 0 y 60 días
        y = np.clip(y, 0, 60)
        
        return X, y