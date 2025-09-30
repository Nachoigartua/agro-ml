"""
Modelo de selección de variedades
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from ml.base_model import BaseMLModel
from utils.logger import get_logger

logger = get_logger(__name__)


class VariedadesModel(BaseMLModel):
    """Modelo para recomendar variedades de cultivos"""
    
    def __init__(self):
        super().__init__("variedades_xgb")
        self.variedades_db = self._init_variedades_database()
    
    def _init_variedades_database(self) -> Dict[str, list]:
        """Inicializa base de datos de variedades"""
        return {
            "trigo": [
                {"nombre": "Klein Dragón", "ciclo": "largo", "calidad": "alta"},
                {"nombre": "Baguette Premium", "ciclo": "intermedio", "calidad": "muy_alta"},
                {"nombre": "SY 100", "ciclo": "corto", "calidad": "media"}
            ],
            "soja": [
                {"nombre": "DM 4670", "ciclo": "largo", "calidad": "alta"},
                {"nombre": "NA 5009", "ciclo": "intermedio", "calidad": "alta"},
                {"nombre": "Nidera A 4910", "ciclo": "corto", "calidad": "media"}
            ],
            "maiz": [
                {"nombre": "DK 7210", "ciclo": "largo", "calidad": "muy_alta"},
                {"nombre": "ACA 417", "ciclo": "intermedio", "calidad": "alta"},
                {"nombre": "P1630", "ciclo": "corto", "calidad": "media"}
            ]
        }
    
    async def train(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entrena el modelo de variedades"""
        from ml.variedades.trainer import VariedadesTrainer
        
        trainer = VariedadesTrainer()
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
        """Genera recomendación de variedades"""
        
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
            
            # Preparar features
            features = self._prepare_features(
                data["cultivo"],
                lote_data,
                clima_data,
                suelo_data,
                data.get("objetivo_productivo", "rendimiento")
            )
            
            # Hacer predicción
            if self.preprocessor:
                features_processed = self.preprocessor.transform(features)
            else:
                features_processed = features
            
            prediction = self.model.predict(features_processed)[0]
            probabilities = self.model.predict_proba(features_processed)[0]
            
            # Obtener variedades disponibles
            variedades = self.variedades_db.get(data["cultivo"].lower(), [])
            if not variedades:
                variedades = [{"nombre": "Variedad Estándar", "ciclo": "intermedio", "calidad": "media"}]
            
            # Seleccionar variedad principal
            variedad_principal = variedades[int(prediction) % len(variedades)]
            
            # Generar alternativas
            alternativas = self._generate_alternatives(
                variedades, variedad_principal, probabilities
            )
            
            return {
                "lote_id": data["lote_id"],
                "tipo_prediccion": "variedades",
                "recomendacion_principal": {
                    "variedad": variedad_principal["nombre"],
                    "ciclo": variedad_principal["ciclo"],
                    "calidad": variedad_principal["calidad"],
                    "confianza": float(probabilities.max())
                },
                "alternativas": alternativas,
                "nivel_confianza": float(probabilities.max()),
                "factores_considerados": [
                    "Zona agroclimática",
                    "Tipo de suelo",
                    "Objetivo productivo",
                    "Historial del lote",
                    "Disponibilidad de agua"
                ],
                "fecha_generacion": datetime.utcnow(),
                "metadata": {
                    "cultivo": data["cultivo"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de variedades: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, cultivo: str, lote_data: Dict,
                         clima_data: list, suelo_data: Dict, objetivo: str) -> pd.DataFrame:
        """Prepara features para el modelo"""
        
        temps = [c.get("temperatura_media", 18) for c in clima_data]
        precips = [c.get("precipitacion", 80) for c in clima_data]
        
        features = pd.DataFrame([{
            "zona_agroclimatica": int(abs(lote_data["latitud"])),
            "tipo_suelo_encoded": self._encode_tipo_suelo(suelo_data.get("textura", "franco")),
            "disponibilidad_agua": np.mean(precips) if precips else 80.0,
            "objetivo_encoded": self._encode_objetivo(objetivo),
            "temp_media_ciclo": np.mean(temps) if temps else 18.0,
            "ph_suelo": suelo_data.get("ph", 6.5),
            "cultivo_encoded": self._encode_cultivo(cultivo)
        }])
        
        return features
    
    def _encode_cultivo(self, cultivo: str) -> int:
        cultivos = {"trigo": 0, "soja": 1, "maiz": 2, "cebada": 3, "girasol": 4}
        return cultivos.get(cultivo.lower(), 0)
    
    def _encode_tipo_suelo(self, tipo: str) -> int:
        tipos = {"arenoso": 0, "franco": 1, "arcilloso": 2}
        return tipos.get(tipo.lower(), 1)
    
    def _encode_objetivo(self, objetivo: str) -> int:
        objetivos = {"rendimiento": 0, "calidad": 1, "estabilidad": 2}
        return objetivos.get(objetivo.lower(), 0)
    
    def _generate_alternatives(self, variedades: list, principal: Dict, 
                              probabilities: np.ndarray) -> list:
        """Genera variedades alternativas"""
        alternativas = []
        
        for i, var in enumerate(variedades):
            if var["nombre"] != principal["nombre"]:
                conf = float(probabilities[i % len(probabilities)])
                alternativas.append({
                    "variedad": var["nombre"],
                    "ciclo": var["ciclo"],
                    "calidad": var["calidad"],
                    "confianza": conf,
                    "pros": self._get_pros(var),
                    "contras": self._get_contras(var)
                })
        
        return alternativas[:2]  # Máximo 2 alternativas
    
    def _get_pros(self, variedad: Dict) -> list:
        pros_map = {
            "largo": ["Mayor potencial de rendimiento", "Mejor aprovechamiento de recursos"],
            "intermedio": ["Balance rendimiento/estabilidad", "Adaptable"],
            "corto": ["Menor riesgo climático", "Cosecha temprana"]
        }
        return pros_map.get(variedad["ciclo"], ["Características estándar"])
    
    def _get_contras(self, variedad: Dict) -> list:
        contras_map = {
            "largo": ["Mayor riesgo climático", "Requiere más insumos"],
            "intermedio": ["Rendimiento moderado"],
            "corto": ["Menor potencial de rendimiento"]
        }
        return contras_map.get(variedad["ciclo"], ["Sin contras significativos"])