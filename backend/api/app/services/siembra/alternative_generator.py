"""Generador de alternativas de siembra basadas en escenarios climáticos."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import pandas as pd

from ...core.logging import get_logger
from ..climate_scenarios import ClimateScenarioGenerator
from .predictor import SiembraPredictor
from .date_converter import DateConverter


logger = get_logger("siembra.alternative_generator")


class AlternativeGenerator:
    """Genera alternativas de siembra usando escenarios climáticos."""

    def __init__(
        self,
        predictor: SiembraPredictor,
        feature_order: list[str],
        date_converter: DateConverter,
    ):
        """Inicializa el generador de alternativas.
        
        Args:
            predictor: Predictor de siembra
            feature_order: Orden de features del modelo
            date_converter: Conversor de fechas
        """
        self._predictor = predictor
        self._feature_order = feature_order
        self._date_converter = date_converter

    def generate(self, feature_row: Dict[str, Any], target_year: int, confianza: float) -> Dict[str, Any]:
        """Genera una alternativa de siembra basada en un escenario climático extremo.
        
        Args:
            feature_row: Features originales del lote
            target_year: Año objetivo para la siembra
            
        Returns:
            Diccionario con la alternativa generada
        """
        # Obtener escenario climático aleatorio
        scenario = ClimateScenarioGenerator.get_random_scenario()
        
        logger.debug(
            "Generando alternativa con escenario climático",
            extra={
                "scenario_name": scenario.nombre,
                "precip_factor": scenario.precip_factor,
                "temp_adjustment": scenario.temp_adjustment,
            }
        )
        
        # Aplicar modificaciones del escenario a las features
        modified_row = ClimateScenarioGenerator.apply_scenario_to_features(
            feature_row, 
            scenario
        )
        
        # Predecir con el modelo usando las features modificadas
        df = pd.DataFrame([modified_row], columns=self._feature_order)
        alt_day = self._predictor.predict_day_of_year(df)
        fecha_alternativa = self._date_converter.day_of_year_to_date(alt_day, target_year)
        
        # Generar ventana de siembra
        ventana = self._date_converter.create_window(fecha_alternativa)
        
        # Obtener pros y contras del escenario
        pros, contras = ClimateScenarioGenerator.get_pros_contras(scenario.nombre)
        
        return {
            "fecha": self._date_converter.date_to_string(fecha_alternativa),
            "ventana": ventana,
            "confianza": confianza,
            "pros": pros,
            "contras": contras,
            "escenario_climatico": {
                "nombre": scenario.nombre,
                "descripcion": scenario.descripcion,
                "modificaciones": {
                    "factor_precipitacion": round(scenario.precip_factor, 2),
                    "ajuste_temperatura_c": round(scenario.temp_adjustment, 1),
                },
            },
        }