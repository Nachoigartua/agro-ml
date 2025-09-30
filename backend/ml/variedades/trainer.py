"""
Trainer para el modelo de variedades
"""
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class VariedadesTrainer:
    """Entrenador del modelo de variedades"""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
    
    async def train_model(self) -> dict:
        """Entrena el modelo con datos sintéticos"""
        
        logger.info("Generando datos de entrenamiento para modelo de variedades...")
        
        X, y = self._generate_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.preprocessor = StandardScaler()
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        logger.info("Entrenando XGBoost Classifier...")
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss'
        )
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        metrics = {
            "accuracy": float(accuracy),
            "f1_score": float(f1),
            "n_samples": len(X),
            "n_classes": len(np.unique(y))
        }
        
        logger.info(f"Modelo entrenado - Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        return metrics
    
    def _generate_training_data(self, n_samples: int = 1000) -> tuple:
        """Genera datos sintéticos para entrenamiento"""
        
        np.random.seed(42)
        
        data = {
            "zona_agroclimatica": np.random.randint(25, 40, n_samples),
            "tipo_suelo_encoded": np.random.randint(0, 3, n_samples),
            "disponibilidad_agua": np.random.uniform(40, 200, n_samples),
            "objetivo_encoded": np.random.randint(0, 3, n_samples),
            "temp_media_ciclo": np.random.uniform(12, 24, n_samples),
            "ph_suelo": np.random.uniform(5.5, 7.5, n_samples),
            "cultivo_encoded": np.random.randint(0, 5, n_samples)
        }
        
        X = pd.DataFrame(data)
        
        # Target: variedad (0, 1, 2 representan diferentes variedades)
        y = np.zeros(n_samples, dtype=int)
        
        # Lógica simple: ciclo largo para buena agua, corto para poca agua
        for i in range(n_samples):
            if X.iloc[i]["disponibilidad_agua"] > 120:
                y[i] = 0  # Ciclo largo
            elif X.iloc[i]["disponibilidad_agua"] > 80:
                y[i] = 1  # Ciclo intermedio
            else:
                y[i] = 2  # Ciclo corto
        
        # Agregar algo de ruido
        noise_idx = np.random.choice(n_samples, size=int(n_samples * 0.1), replace=False)
        y[noise_idx] = np.random.randint(0, 3, len(noise_idx))
        
        return X, y