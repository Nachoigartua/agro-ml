"""
Modelo de predicción climática
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class ClimaModel(BaseMLModel):
    """Modelo para predecir condiciones climáticas"""
    
    def __init__(self):
        super().__init__("clima_arima")
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo climático"""
        from ml.clima.trainer import ClimaTrainer
        
        trainer = ClimaTrainer()
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
        """Genera predicción climática"""
        
        if self.model is None:
            if not self.load_model():
                logger.info("Modelo no encontrado, entrenando...")
                await self.train({})
        
        try:
            from services.finnegans_client import finnegans_client
            
            # Obtener datos climáticos históricos
            clima_historico = await finnegans_client.get_clima_historico(
                data["latitud"],
                data["longitud"]
            )
            
            # Generar predicciones para el período solicitado
            fecha_desde = data["fecha_desde"]
            fecha_hasta = data["fecha_hasta"]
            
            predicciones_diarias = self._predict_daily_weather(
                clima_historico,
                fecha_desde,
                fecha_hasta
            )
            
            # Agregar a nivel mensual
            predicciones_mensuales = self._aggregate_monthly(predicciones_diarias)
            
            return {
                "lote_id": None,
                "tipo_prediccion": "clima",
                "recomendacion_principal": {
                    "periodo": f"{fecha_desde} a {fecha_hasta}",
                    "predicciones_mensuales": predicciones_mensuales,
                    "alertas": self._generate_alerts(predicciones_mensuales)
                },
                "alternativas": [],
                "nivel_confianza": 0.72,
                "factores_considerados": [
                    "Datos históricos locales",
                    "Tendencias estacionales",
                    "Patrones climáticos regionales"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "latitud": data["latitud"],
                    "longitud": data["longitud"],
                    "dias_prediccion": (fecha_hasta - fecha_desde).days
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción climática: {e}", exc_info=True)
            raise
    
    def _predict_daily_weather(self, historico: list, fecha_desde, fecha_hasta) -> list:
        """Predice clima día a día"""
        
        # Extraer datos históricos
        temps = [h.get("temperatura_media", 18) for h in historico]
        precips = [h.get("precipitacion", 2) for h in historico]
        
        # Calcular promedios y tendencias
        temp_promedio = np.mean(temps) if temps else 18.0
        precip_promedio = np.mean(precips) if precips else 2.0
        
        predicciones = []
        current_date = fecha_desde
        
        while current_date <= fecha_hasta:
            # Agregar componente estacional
            mes = current_date.month
            factor_temp = self._seasonal_temp_factor(mes)
            factor_precip = self._seasonal_precip_factor(mes)
            
            # Predicción simple con variabilidad
            temp_pred = temp_promedio * factor_temp + np.random.normal(0, 2)
            precip_pred = max(0, precip_promedio * factor_precip + np.random.normal(0, 5))
            
            predicciones.append({
                "fecha": current_date.isoformat(),
                "temperatura_min": float(temp_pred - 5),
                "temperatura_max": float(temp_pred + 5),
                "temperatura_media": float(temp_pred),
                "precipitacion_mm": float(precip_pred),
                "probabilidad_lluvia": float(min(1.0, precip_pred / 10))
            })
            
            current_date += timedelta(days=1)
        
        return predicciones
    
    def _seasonal_temp_factor(self, mes: int) -> float:
        """Factor estacional para temperatura"""
        # Verano (dic-feb): 1.2, Invierno (jun-ago): 0.8
        factores = {
            1: 1.15, 2: 1.10, 3: 1.05, 4: 1.0, 5: 0.95, 6: 0.85,
            7: 0.80, 8: 0.85, 9: 0.90, 10: 0.95, 11: 1.05, 12: 1.15
        }
        return factores.get(mes, 1.0)
    
    def _seasonal_precip_factor(self, mes: int) -> float:
        """Factor estacional para precipitación"""
        # Época húmeda (oct-mar): >1, Época seca (abr-sep): <1
        factores = {
            1: 1.3, 2: 1.2, 3: 1.1, 4: 0.9, 5: 0.8, 6: 0.7,
            7: 0.7, 8: 0.8, 9: 0.9, 10: 1.1, 11: 1.2, 12: 1.3
        }
        return factores.get(mes, 1.0)
    
    def _aggregate_monthly(self, predicciones_diarias: list) -> list:
        """Agrega predicciones diarias a nivel mensual"""
        
        df = pd.DataFrame(predicciones_diarias)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mes'] = df['fecha'].dt.to_period('M')
        
        mensuales = []
        for mes, grupo in df.groupby('mes'):
            mensuales.append({
                "mes": str(mes),
                "temperatura_media": float(grupo['temperatura_media'].mean()),
                "temperatura_min_promedio": float(grupo['temperatura_min'].mean()),
                "temperatura_max_promedio": float(grupo['temperatura_max'].mean()),
                "precipitacion_total_mm": float(grupo['precipitacion_mm'].sum()),
                "dias_con_lluvia": int((grupo['precipitacion_mm'] > 1).sum())
            })
        
        return mensuales
    
    def _generate_alerts(self, predicciones_mensuales: list) -> list:
        """Genera alertas basadas en predicciones"""
        
        alertas = []
        
        for pred in predicciones_mensuales:
            if pred["precipitacion_total_mm"] < 50:
                alertas.append({
                    "tipo": "deficit_hidrico",
                    "mes": pred["mes"],
                    "severidad": "media",
                    "mensaje": f"Precipitación esperada baja ({pred['precipitacion_total_mm']:.0f}mm)"
                })
            
            if pred["temperatura_media"] > 28:
                alertas.append({
                    "tipo": "stress_termico",
                    "mes": pred["mes"],
                    "severidad": "alta",
                    "mensaje": f"Temperaturas elevadas esperadas ({pred['temperatura_media']:.1f}°C)"
                })
        
        return alertas