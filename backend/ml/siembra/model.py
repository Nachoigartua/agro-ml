"""
Modelo de predicción de fechas óptimas de siembra
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class SiembraModel(BaseMLModel):
    """Modelo para predecir fechas óptimas de siembra"""
    
    def __init__(self):
        super().__init__("siembra_rf")
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo de siembra"""
        from ml.siembra.trainer import SiembraTrainer
        
        trainer = SiembraTrainer()
        metrics = await trainer.train_model()
        
        # Actualizar modelo y metadata
        self.model = trainer.model
        self.preprocessor = trainer.preprocessor
        self.metadata = {
            "trained_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "metrics": metrics
        }
        
        # Guardar modelo
        self.save_model()
        
        return {
            "status": "success",
            "metrics": metrics,
            "trained_at": self.metadata["trained_at"]
        }
    
    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera recomendación de fecha de siembra"""
        
        # Si el modelo no está cargado, cargar o entrenar
        if self.model is None:
            if not self.load_model():
                logger.info("Modelo no encontrado, entrenando...")
                await self.train({})
        
        try:
            # Obtener datos del lote y clima
            from services.finnegans_client import finnegans_client
            
            lote_data = await finnegans_client.get_lote_data(data["lote_id"])
            clima_data = await finnegans_client.get_clima_historico(
                lote_data["latitud"],
                lote_data["longitud"]
            )
            suelo_data = await finnegans_client.get_caracteristicas_suelo(data["lote_id"])
            
            # Preparar features
            features = self._prepare_features(
                data["cultivo"],
                lote_data,
                clima_data,
                suelo_data
            )
            
            # Hacer predicción
            if self.preprocessor:
                features_processed = self.preprocessor.transform(features)
            else:
                features_processed = features
            
            prediction = self.model.predict(features_processed)[0]
            confidence = self.model.predict_proba(features_processed).max()
            
            # Calcular fecha óptima
            fecha_optima = self._calculate_optimal_date(prediction, data["cultivo"])
            ventana_siembra = self._calculate_window(fecha_optima)
            
            # Generar alternativas
            alternativas = self._generate_alternatives(fecha_optima, data["cultivo"])
            
            return {
                "lote_id": data["lote_id"],
                "tipo_prediccion": "siembra",
                "recomendacion_principal": {
                    "fecha_optima": fecha_optima.isoformat(),
                    "ventana": ventana_siembra,
                    "confianza": float(confidence)
                },
                "alternativas": alternativas,
                "nivel_confianza": float(confidence),
                "factores_considerados": [
                    "Temperatura histórica",
                    "Precipitaciones esperadas",
                    "Tipo de suelo",
                    "Cultivo y variedad",
                    "Historial del lote"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "cultivo": data["cultivo"],
                    "campana": data.get("campana", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de siembra: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, cultivo: str, lote_data: Dict, 
                         clima_data: list, suelo_data: Dict) -> pd.DataFrame:
        """Prepara features para el modelo"""
        
        # Calcular estadísticas climáticas
        temps = [c["temperatura_media"] for c in clima_data if "temperatura_media" in c]
        precips = [c["precipitacion"] for c in clima_data if "precipitacion" in c]
        
        features = pd.DataFrame([{
            "latitud": lote_data["latitud"],
            "longitud": lote_data["longitud"],
            "temp_media": np.mean(temps) if temps else 18.0,
            "temp_std": np.std(temps) if temps else 5.0,
            "precipitacion_media": np.mean(precips) if precips else 80.0,
            "ph_suelo": suelo_data.get("ph", 6.5),
            "materia_organica": suelo_data.get("materia_organica", 3.0),
            "cultivo_encoded": self._encode_cultivo(cultivo),
            "mes": datetime.now().month
        }])
        
        return features
    
    def _encode_cultivo(self, cultivo: str) -> int:
        """Codifica el cultivo como número"""
        cultivos = {"trigo": 0, "soja": 1, "maiz": 2, "cebada": 3, "girasol": 4}
        return cultivos.get(cultivo.lower(), 0)
    
    def _calculate_optimal_date(self, prediction: float, cultivo: str) -> datetime:
        """Calcula la fecha óptima basada en la predicción"""
        # prediction es el día del año óptimo
        year = datetime.now().year
        if datetime.now().month > 6:
            year += 1
        
        fecha_base = datetime(year, 1, 1)
        fecha_optima = fecha_base + timedelta(days=int(prediction))
        
        return fecha_optima
    
    def _calculate_window(self, fecha_optima: datetime) -> list:
        """Calcula la ventana de siembra"""
        fecha_inicio = fecha_optima - timedelta(days=7)
        fecha_fin = fecha_optima + timedelta(days=7)
        
        return [fecha_inicio.isoformat(), fecha_fin.isoformat()]
    
    def _generate_alternatives(self, fecha_optima: datetime, cultivo: str) -> list:
        """Genera fechas alternativas"""
        alternativa_1 = fecha_optima + timedelta(days=14)
        alternativa_2 = fecha_optima - timedelta(days=14)
        
        return [
            {
                "fecha": alternativa_1.isoformat(),
                "confianza": 0.75,
                "pros": ["Mayor humedad esperada", "Menor presión de plagas"],
                "contras": ["Ciclo más corto", "Riesgo de heladas tardías"]
            },
            {
                "fecha": alternativa_2.isoformat(),
                "confianza": 0.70,
                "pros": ["Ciclo más largo", "Mejor aprovechamiento de lluvias"],
                "contras": ["Mayor riesgo de heladas tempranas", "Menor humedad"]
            }
        ]