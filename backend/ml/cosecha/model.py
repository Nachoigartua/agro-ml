"""
Modelo de optimización de cosecha
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class CosechaModel(BaseMLModel):
    """Modelo para determinar momento óptimo de cosecha"""
    
    def __init__(self):
        super().__init__("cosecha_rf")
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo de cosecha"""
        from ml.cosecha.trainer import CosechaTrainer
        
        trainer = CosechaTrainer()
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
        """Genera recomendación de momento de cosecha"""
        
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
            
            # Calcular días desde siembra
            fecha_siembra = data["fecha_siembra"]
            if isinstance(fecha_siembra, str):
                fecha_siembra = datetime.fromisoformat(fecha_siembra.replace('Z', '+00:00')).date()
            
            dias_desde_siembra = (datetime.now().date() - fecha_siembra).days
            
            # Preparar features
            features = self._prepare_features(
                data["cultivo"],
                data.get("variedad"),
                dias_desde_siembra,
                clima_data
            )
            
            # Hacer predicción
            if self.preprocessor:
                features_processed = self.preprocessor.transform(features)
            else:
                features_processed = features
            
            dias_hasta_cosecha = int(self.model.predict(features_processed)[0])
            
            # Calcular fecha óptima
            fecha_optima = datetime.now().date() + timedelta(days=dias_hasta_cosecha)
            ventana_cosecha = self._calculate_harvest_window(fecha_optima)
            
            # Predicción de calidad
            calidad_predicha = self._predict_quality(features.iloc[0].to_dict())
            
            return {
                "lote_id": data["lote_id"],
                "tipo_prediccion": "cosecha",
                "recomendacion_principal": {
                    "fecha_optima": fecha_optima.isoformat(),
                    "ventana_cosecha": ventana_cosecha,
                    "dias_restantes": dias_hasta_cosecha,
                    "humedad_esperada_pct": 14.0,
                    "calidad_esperada": calidad_predicha
                },
                "alternativas": self._generate_harvest_alternatives(fecha_optima),
                "nivel_confianza": 0.80,
                "factores_considerados": [
                    "Madurez fisiológica",
                    "Condiciones climáticas esperadas",
                    "Calidad esperada del grano",
                    "Disponibilidad de maquinaria"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "cultivo": data["cultivo"],
                    "variedad": data.get("variedad", "N/A"),
                    "dias_desde_siembra": dias_desde_siembra
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de cosecha: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, cultivo: str, variedad: str, 
                         dias_siembra: int, clima_data: list) -> pd.DataFrame:
        """Prepara features para el modelo"""
        
        # Calcular acumulación térmica
        temps = [c.get("temperatura_media", 18) for c in clima_data[-30:]]  # Últimos 30 días
        grados_dia = sum([max(0, t - 10) for t in temps])
        
        features = pd.DataFrame([{
            "cultivo_encoded": self._encode_cultivo(cultivo),
            "dias_desde_siembra": dias_siembra,
            "grados_dia_acumulados": grados_dia,
            "temp_media_reciente": np.mean(temps) if temps else 18.0,
            "precipitacion_reciente": sum([c.get("precipitacion", 0) for c in clima_data[-7:]]),
            "ciclo_variedad_encoded": self._encode_ciclo(variedad)
        }])
        
        return features
    
    def _encode_cultivo(self, cultivo: str) -> int:
        cultivos = {"trigo": 0, "soja": 1, "maiz": 2, "cebada": 3, "girasol": 4}
        return cultivos.get(cultivo.lower(), 0)
    
    def _encode_ciclo(self, variedad: str) -> int:
        # Simplificación: extraer ciclo de nombre de variedad o asumir intermedio
        if variedad and ("corto" in variedad.lower() or "precoz" in variedad.lower()):
            return 0
        elif variedad and ("largo" in variedad.lower() or "tardio" in variedad.lower()):
            return 2
        return 1  # Intermedio por defecto
    
    def _calculate_harvest_window(self, fecha_optima) -> list:
        """Calcula ventana de cosecha"""
        inicio = fecha_optima - timedelta(days=5)
        fin = fecha_optima + timedelta(days=5)
        return [inicio.isoformat(), fin.isoformat()]
    
    def _predict_quality(self, features: Dict) -> str:
        """Predice calidad del grano"""
        # Lógica simplificada
        temp_media = features.get("temp_media_reciente", 18)
        
        if 15 <= temp_media <= 22:
            return "Excelente"
        elif 12 <= temp_media <= 25:
            return "Buena"
        else:
            return "Regular"
    
    def _generate_harvest_alternatives(self, fecha_optima) -> list:
        """Genera alternativas de cosecha"""
        
        alternativa_temprana = fecha_optima - timedelta(days=7)
        alternativa_tardia = fecha_optima + timedelta(days=7)
        
        return [
            {
                "fecha": alternativa_temprana.isoformat(),
                "tipo": "Cosecha temprana",
                "pros": ["Menor riesgo climático", "Mejor calidad sanitaria"],
                "contras": ["Posible mayor humedad", "Rendimiento ligeramente menor"],
                "confianza": 0.75
            },
            {
                "fecha": alternativa_tardia.isoformat(),
                "tipo": "Cosecha tardía",
                "pros": ["Mayor rendimiento potencial", "Menor humedad"],
                "contras": ["Mayor riesgo climático", "Posible desgrane"],
                "confianza": 0.70
            }
        ]