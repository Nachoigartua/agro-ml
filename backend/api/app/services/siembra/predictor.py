"""Lógica de predicción de siembra."""
from __future__ import annotations

from typing import Any

from ...core.logging import get_logger


logger = get_logger("siembra.predictor")


class SiembraPredictor:
    """Ejecuta predicciones usando el modelo de siembra."""

    def __init__(self, model: Any, preprocessor: Any):
        """Inicializa el predictor.
        
        Args:
            model: Modelo ML entrenado
            preprocessor: Preprocessor para transformar features
        """
        self._model = model
        self._preprocessor = preprocessor

    def predict_day_of_year(self, features_df) -> int:
        """Predice el día del año óptimo para siembra.
        
        Args:
            features_df: DataFrame con las features preprocesadas
            
        Returns:
            Día del año (1-365) como entero
        """
        transformed = self._preprocessor.transform(features_df)
        prediction = float(self._model.predict(transformed)[0])
        return self._clamp_day_of_year(prediction)

    def _clamp_day_of_year(self, value: float) -> int:
        """Asegura que el día del año esté en rango válido.
        
        Args:
            value: Valor predicho (puede estar fuera de rango)
            
        Returns:
            Día del año entre 1 y 365
        """
        day = int(round(value))
        
        if day < 1:
            logger.warning(
                "Predicción por debajo del rango válido",
                extra={"predicted_day": day, "original_value": value, "clamped_to": 1}
            )
            return 1
        
        if day > 365:
            logger.warning(
                "Predicción por encima del rango válido",
                extra={"predicted_day": day, "original_value": value, "clamped_to": 365}
            )
            return 365
        
        return day