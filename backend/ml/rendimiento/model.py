"""
Modelo de predicción de rendimientos
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class RendimientoModel(BaseMLModel):
    """Modelo para predecir rendimientos de cultivos"""
    
    def __init__(self):
        super().__init__("rendimiento_gbr")
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo de rendimiento"""
        from ml.rendimiento.trainer import RendimientoTrainer
        
        trainer = RendimientoTrainer()
        metrics = await trainer.train_model()
        
        self.model = trainer.model
        self.preprocessor = trainer.preprocessor
        self.metadata = {
            "trained_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "metrics": metrics
        }
        
        self.save_model()
        
        return {
            "status": "success",
            "metrics": metrics,
            "trained_at": self.metadata["trained_at"]
        }
    
    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera predicción de rendimiento"""
        
        if self.model is None:
            if not self.load_model():
                logger.info("Modelo no encontrado, entrenando...")
                await self.train({})
        
        try:
            from services.finnegans_client import finnegans_client
            
            lote_data = await finnegans_client.get_lote_data(data["lote_id"])
            clima_data = await finnegans_client.get_clima_historico(
                lote_data["latitud"],
                lote_data["longitud"]
            )
            suelo_data = await finnegans_client.get_caracteristicas_suelo(data["lote_id"])
            historial = await finnegans_client.get_cosechas_historicas(data["lote_id"])
            
            # Preparar features
            features = self._prepare_features(
                data["cultivo"],
                data.get("fecha_siembra"),
                data.get("variedad"),
                lote_data,
                clima_data,
                suelo_data,
                historial
            )
            
            # Hacer predicción
            if self.preprocessor:
                features_processed = self.preprocessor.transform(features)
            else:
                features_processed = features
            
            prediction = self.model.predict(features_processed)[0]
            
            # Calcular intervalo de confianza
            std_error = self._estimate_prediction_std(features_processed)
            confidence_interval = [
                max(0, prediction - 1.96 * std_error),
                prediction + 1.96 * std_error
            ]
            
            # Calcular factores limitantes
            factores_limitantes = self._identify_limiting_factors(
                features.iloc[0].to_dict(), prediction
            )
            
            return {
                "lote_id": data["lote_id"],
                "tipo_prediccion": "rendimiento",
                "recomendacion_principal": {
                    "rendimiento_esperado_kg_ha": float(prediction),
                    "intervalo_confianza": [float(x) for x in confidence_interval],
                    "unidad": "kg/ha"
                },
                "alternativas": [],
                "nivel_confianza": 0.85,
                "factores_considerados": [
                    "Manejo del cultivo",
                    "Condiciones climáticas esperadas",
                    "Características del suelo",
                    "Historial del lote",
                    "Variedad seleccionada"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "cultivo": data["cultivo"],
                    "variedad": data.get("variedad", "N/A"),
                    "factores_limitantes": factores_limitantes
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de rendimiento: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, cultivo: str, fecha_siembra, variedad: str,
                         lote_data: Dict, clima_data: list, suelo_data: Dict,
                         historial: list) -> pd.DataFrame:
        """Prepara features para el modelo"""
        
        temps = [c.get("temperatura_media", 18) for c in clima_data]
        precips = [c.get("precipitacion", 80) for c in clima_data]
        
        # Calcular rendimiento histórico promedio
        rend_hist = [h.get("rendimiento", 3000) for h in historial if "rendimiento" in h]
        rend_promedio = np.mean(rend_hist) if rend_hist else 3000
        
        features = pd.DataFrame([{
            "cultivo_encoded": self._encode_cultivo(cultivo),
            "temp_media_ciclo": np.mean(temps) if temps else 18.0,
            "precipitacion_ciclo": np.sum(precips) if precips else 400.0,
            "ph_suelo": suelo_data.get("ph", 6.5),
            "materia_organica": suelo_data.get("materia_organica", 3.0),
            "nitrogeno": suelo_data.get("nitrogeno", 20.0),
            "fosforo": suelo_data.get("fosforo", 15.0),
            "potasio": suelo_data.get("potasio", 200.0),
            "rendimiento_historico": rend_promedio,
            "superficie_ha": lote_data.get("superficie_ha", 100.0)
        }])
        
        return features
    
    def _encode_cultivo(self, cultivo: str) -> int:
        cultivos = {"trigo": 0, "soja": 1, "maiz": 2, "cebada": 3, "girasol": 4}
        return cultivos.get(cultivo.lower(), 0)
    
    def _estimate_prediction_std(self, features: np.ndarray) -> float:
        """Estima la desviación estándar de la predicción"""
        # Aproximación simple: 10% del valor predicho
        return 300.0
    
    def _identify_limiting_factors(self, features: Dict, prediction: float) -> list:
        """Identifica factores limitantes del rendimiento"""
        limitantes = []
        
        if features.get("precipitacion_ciclo", 0) < 300:
            limitantes.append("Déficit hídrico esperado")
        
        if features.get("nitrogeno", 0) < 15:
            limitantes.append("Bajo nivel de nitrógeno")
        
        if features.get("ph_suelo", 7) < 6.0 or features.get("ph_suelo", 7) > 7.5:
            limitantes.append("pH del suelo no óptimo")
        
        if features.get("materia_organica", 0) < 2.5:
            limitantes.append("Baja materia orgánica")
        
        return limitantes if limitantes else ["Ningún factor limitante identificado"]