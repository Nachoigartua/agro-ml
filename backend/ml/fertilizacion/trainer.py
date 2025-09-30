"""
Trainer para el modelo de fertilización
"""
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class FertilizacionTrainer:
    """Entrenador del modelo de fertilización"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo de fertilización...")
        
        X, y = self._generate_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.preprocessor = StandardScaler()
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        logger.info("Entrenando Multi-Output Regressor...")
        base_model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42
        )
        self.model = MultiOutputRegressor(base_model)
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        
        # Calcular métricas para cada salida (N, P, K)
        rmse_n = np.sqrt(mean_squared_error(y_test[:, 0], y_pred[:, 0]))
        rmse_p = np.sqrt(mean_squared_error(y_test[:, 1], y_pred[:, 1]))
        rmse_k = np.sqrt(mean_squared_error(y_test[:, 2], y_pred[:, 2]))
        
        r2_n = r2_score(y_test[:, 0], y_pred[:, 0])
        r2_p = r2_score(y_test[:, 1], y_pred[:, 1])
        r2_k = r2_score(y_test[:, 2], y_pred[:, 2])
        
        metrics = {
            "rmse_nitrogen": float(rmse_n),
            "rmse_phosphorus": float(rmse_p),
            "rmse_potassium": float(rmse_k),
            "r2_nitrogen": float(r2_n),
            "r2_phosphorus": float(r2_p),
            "r2_potassium": float(r2_k),
            "n_samples": len(X)
        }
        
        logger.info(f"Modelo entrenado - RMSE N: {rmse_n:.1f}, P: {rmse_p:.1f}, K: {rmse_k:.1f}")
        
        return metrics
    
    def _generate_training_data(self, n_samples: int = 1000) -> tuple:
        """Genera datos sintéticos para entrenamiento"""
        
        np.random.seed(42)
        
        data = {
            "cultivo_encoded": np.random.randint(0, 5, n_samples),
            "objetivo_rendimiento": np.random.uniform(2000, 6000, n_samples),
            "n_actual": np.random.uniform(10, 40, n_samples),
            "p_actual": np.random.uniform(8, 30, n_samples),
            "k_actual": np.random.uniform(100, 300, n_samples),
            "ph_suelo": np.random.uniform(5.5, 7.5, n_samples),
            "materia_organica": np.random.uniform(1.5, 5, n_samples),
            "textura_encoded": np.random.randint(0, 3, n_samples)
        }
        
        X = pd.DataFrame(data)
        
        # Targets: dosis de N, P, K en kg/ha
        # Fórmula simplificada basada en extracción del cultivo
        n_requerido = (X["objetivo_rendimiento"] / 100) * 2.5 - X["n_actual"]
        p_requerido = (X["objetivo_rendimiento"] / 100) * 0.8 - X["p_actual"] * 0.5
        k_requerido = (X["objetivo_rendimiento"] / 100) * 1.5 - X["k_actual"] * 0.1
        
        # Agregar variabilidad
        n_requerido += np.random.normal(0, 10, n_samples)
        p_requerido += np.random.normal(0, 5, n_samples)
        k_requerido += np.random.normal(0, 15, n_samples)
        
        # Limitar valores razonables
        n_requerido = np.clip(n_requerido, 50, 200)
        p_requerido = np.clip(p_requerido, 20, 80)
        k_requerido = np.clip(k_requerido, 30, 150)
        
        y = np.column_stack([n_requerido, p_requerido, k_requerido])
        
        return X, y