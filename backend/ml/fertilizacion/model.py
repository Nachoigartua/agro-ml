"""
Modelo de optimización de fertilización
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class FertilizacionModel(BaseMLModel):
    """Modelo para optimizar planes de fertilización"""
    
    def __init__(self):
        super().__init__("fertilizacion_multi")
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo de fertilización"""
        from ml.fertilizacion.trainer import FertilizacionTrainer
        
        trainer = FertilizacionTrainer()
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
        """Genera plan de fertilización optimizado"""
        
        if self.model is None:
            if not self.load_model():
                logger.info("Modelo no encontrado, entrenando...")
                await self.train({})
        
        try:
            from services.finnegans_client import finnegans_client
            
            lote_data = await finnegans_client.get_lote_data(data["lote_id"])
            suelo_data = await finnegans_client.get_caracteristicas_suelo(data["lote_id"])
            
            # Preparar features
            features = self._prepare_features(
                data["cultivo"],
                data.get("objetivo_rendimiento"),
                lote_data,
                suelo_data
            )
            
            # Hacer predicción (devuelve N, P, K)
            if self.preprocessor:
                features_processed = self.preprocessor.transform(features)
            else:
                features_processed = features
            
            predictions = self.model.predict(features_processed)[0]
            
            # Convertir a plan de fertilización
            plan_principal = self._create_fertilization_plan(
                predictions, data["cultivo"], lote_data["superficie_ha"]
            )
            
            # Generar alternativas
            alternativas = self._generate_alternative_plans(
                predictions, data["cultivo"], lote_data["superficie_ha"]
            )
            
            return {
                "lote_id": data["lote_id"],
                "tipo_prediccion": "fertilizacion",
                "recomendacion_principal": plan_principal,
                "alternativas": alternativas,
                "nivel_confianza": 0.82,
                "factores_considerados": [
                    "Análisis de suelo",
                    "Requerimientos del cultivo",
                    "Objetivo de rendimiento",
                    "Balance nutricional",
                    "Disponibilidad de nutrientes"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "cultivo": data["cultivo"],
                    "superficie_ha": lote_data["superficie_ha"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de fertilización: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, cultivo: str, objetivo_rend: float,
                         lote_data: Dict, suelo_data: Dict) -> pd.DataFrame:
        """Prepara features para el modelo"""
        
        # Si no hay objetivo, estimar basado en histórico
        if objetivo_rend is None:
            objetivo_rend = 3500.0  # Valor por defecto
        
        features = pd.DataFrame([{
            "cultivo_encoded": self._encode_cultivo(cultivo),
            "objetivo_rendimiento": objetivo_rend,
            "n_actual": suelo_data.get("nitrogeno", 20.0),
            "p_actual": suelo_data.get("fosforo", 15.0),
            "k_actual": suelo_data.get("potasio", 200.0),
            "ph_suelo": suelo_data.get("ph", 6.5),
            "materia_organica": suelo_data.get("materia_organica", 3.0),
            "textura_encoded": self._encode_textura(suelo_data.get("textura", "franco"))
        }])
        
        return features
    
    def _encode_cultivo(self, cultivo: str) -> int:
        cultivos = {"trigo": 0, "soja": 1, "maiz": 2, "cebada": 3, "girasol": 4}
        return cultivos.get(cultivo.lower(), 0)
    
    def _encode_textura(self, textura: str) -> int:
        texturas = {"arenoso": 0, "franco": 1, "arcilloso": 2}
        return texturas.get(textura.lower(), 1)
    
    def _create_fertilization_plan(self, predictions: np.ndarray, 
                                   cultivo: str, superficie: float) -> Dict:
        """Crea plan de fertilización detallado"""
        
        n_total, p_total, k_total = predictions
        
        # Dividir en aplicaciones
        aplicaciones = [
            {
                "momento": "siembra",
                "dias_desde_siembra": 0,
                "nitrogeno_kg_ha": float(n_total * 0.3),
                "fosforo_kg_ha": float(p_total * 1.0),  # Todo el P a la siembra
                "potasio_kg_ha": float(k_total * 0.5),
                "producto_sugerido": "Fosfato diamónico (18-46-0)"
            },
            {
                "momento": "macollaje",
                "dias_desde_siembra": 30,
                "nitrogeno_kg_ha": float(n_total * 0.4),
                "fosforo_kg_ha": 0.0,
                "potasio_kg_ha": float(k_total * 0.3),
                "producto_sugerido": "Urea (46-0-0)"
            },
            {
                "momento": "encañazon",
                "dias_desde_siembra": 60,
                "nitrogeno_kg_ha": float(n_total * 0.3),
                "fosforo_kg_ha": 0.0,
                "potasio_kg_ha": float(k_total * 0.2),
                "producto_sugerido": "Urea (46-0-0)"
            }
        ]
        
        # Calcular costo estimado
        costo_ha = self._estimate_cost(n_total, p_total, k_total)
        costo_total = costo_ha * superficie
        
        return {
            "nitrogeno_total_kg_ha": float(n_total),
            "fosforo_total_kg_ha": float(p_total),
            "potasio_total_kg_ha": float(k_total),
            "aplicaciones": aplicaciones,
            "costo_estimado_por_ha_usd": float(costo_ha),
            "costo_total_usd": float(costo_total),
            "confianza": 0.82
        }
    
    def _generate_alternative_plans(self, predictions: np.ndarray,
                                    cultivo: str, superficie: float) -> list:
        """Genera planes alternativos de fertilización"""
        
        n_total, p_total, k_total = predictions
        
        # Plan conservador (80% de dosis)
        plan_conservador = self._create_fertilization_plan(
            predictions * 0.8, cultivo, superficie
        )
        plan_conservador["nombre"] = "Plan Conservador"
        plan_conservador["descripcion"] = "Dosis reducida, menor riesgo"
        
        # Plan intensivo (120% de dosis)
        plan_intensivo = self._create_fertilization_plan(
            predictions * 1.2, cultivo, superficie
        )
        plan_intensivo["nombre"] = "Plan Intensivo"
        plan_intensivo["descripcion"] = "Dosis elevada, mayor potencial"
        
        return [plan_conservador, plan_intensivo]
    
    def _estimate_cost(self, n: float, p: float, k: float) -> float:
        """Estima el costo del plan de fertilización"""
        # Precios aproximados por kg de nutriente (USD)
        precio_n = 0.80
        precio_p = 1.20
        precio_k = 0.60
        
        costo = (n * precio_n) + (p * precio_p) + (k * precio_k)
        return costo