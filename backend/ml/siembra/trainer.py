"""
Trainer para el modelo de siembra
"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class SiembraTrainer:
    """Entrenador del modelo de siembra"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo de siembra...")
        
        # Generar datos sintéticos
        X, y = self._generate_training_data()
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Preprocesar
        self.preprocessor = StandardScaler()
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        # Entrenar modelo
        logger.info("Entrenando Random Forest Regressor...")
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluar
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
        
        # Features
        data = {
            "latitud": np.random.uniform(-38, -28, n_samples),
            "longitud": np.random.uniform(-65, -58, n_samples),
            "temp_media": np.random.uniform(10, 25, n_samples),
            "temp_std": np.random.uniform(3, 8, n_samples),
            "precipitacion_media": np.random.uniform(50, 150, n_samples),
            "ph_suelo": np.random.uniform(5.5, 7.5, n_samples),
            "materia_organica": np.random.uniform(2, 5, n_samples),
            "cultivo_encoded": np.random.randint(0, 5, n_samples),
            "mes": np.random.randint(1, 13, n_samples)
        }
        
        X = pd.DataFrame(data)
        
        # Target: día del año óptimo de siembra
        # Simulación basada en temperatura y precipitación
        y = (
            100 + 
            (X["temp_media"] - 15) * 3 +
            (X["precipitacion_media"] - 80) * 0.2 +
            X["cultivo_encoded"] * 10 +
            np.random.normal(0, 5, n_samples)
        )
        
        # Limitar entre día 60 y 150 (marzo a mayo)
        y = np.clip(y, 60, 150)
        
        return X, y