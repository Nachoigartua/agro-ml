"""Constructor de features para el modelo de siembra."""
from __future__ import annotations

from typing import Any, Dict, Optional

from ...core.logging import get_logger
from ...utils.type_converters import as_float, as_string


logger = get_logger("siembra.feature_builder")


class FeatureBuilder:
    """Construye el vector de features desde los datos del lote."""

    def __init__(
        self,
        feature_order: list[str],
        numeric_defaults: Dict[str, float],
        categorical_defaults: Dict[str, str],
    ):
        """Inicializa el constructor de features.
        
        Args:
            feature_order: Orden de las features esperado por el modelo
            numeric_defaults: Valores por defecto para features numéricas
            categorical_defaults: Valores por defecto para features categóricas
        """
        self._feature_order = feature_order
        self._numeric_defaults = numeric_defaults
        self._categorical_defaults = categorical_defaults
        
        if not self._feature_order:
            raise ValueError("El orden de features no puede estar vacío")

    def build(self, lote_data: Dict[str, Any], cultivo_override: Optional[str] = None) -> Dict[str, Any]:
        """Construye el diccionario de features desde datos del lote.
        
        Args:
            lote_data: Datos del lote (ubicación, suelo, clima)
            cultivo_override: Si se proporciona, sobrescribe cultivo_anterior
            
        Returns:
            Diccionario con todas las features necesarias
            
        Raises:
            ValueError: Si falta una feature requerida sin valor por defecto
        """
        row: Dict[str, Any] = {}
        
        for feature in self._feature_order:
            value = self._extract_feature_value(feature, lote_data)
            
            # Override especial para cultivo_anterior
            if feature == "cultivo_anterior" and cultivo_override is not None:
                value = cultivo_override
            
            # Si no hay valor, usar default
            if value is None:
                value = self._get_default(feature)
            
            row[feature] = value
        
        return row

    def _extract_feature_value(self, feature: str, lote_data: Dict[str, Any]) -> Optional[Any]:
        """Extrae el valor de una feature desde los datos del lote.
        
        Args:
            feature: Nombre de la feature
            lote_data: Datos del lote
            
        Returns:
            Valor de la feature o None si no existe
        """
        ubicacion = lote_data.get("ubicacion") or {}
        suelo = lote_data.get("suelo") or {}
        clima = lote_data.get("clima") or {}

        # Features de ubicación
        if feature == "latitud":
            return as_float(ubicacion.get("latitud"))
        if feature == "longitud":
            return as_float(ubicacion.get("longitud"))

        # Features de suelo
        if feature == "tipo_suelo":
            return as_string(suelo.get("tipo_suelo"))
        if feature == "ph_suelo":
            return as_float(suelo.get("ph_suelo"))
        if feature == "materia_organica_pct":
            # Usar materia_organica_pct preferentemente, fallback a materia_organica
            value = suelo.get("materia_organica_pct") or suelo.get("materia_organica")
            return as_float(value)

        # Features de clima (precipitación)
        if feature.startswith("precipitacion_"):
            return as_float(clima.get(feature))

        # Cultivo anterior se maneja especialmente
        if feature == "cultivo_anterior":
            return None  # Se sobrescribe luego con el cultivo del request

        # Búsqueda genérica en lote_data o clima
        if feature in lote_data:
            return self._coerce_value(feature, lote_data[feature])
        if feature in clima:
            return self._coerce_value(feature, clima[feature])

        return None

    def _coerce_value(self, feature: str, value: Any) -> Optional[Any]:
        """Fuerza el tipo del valor según el tipo de feature.
        
        Args:
            feature: Nombre de la feature
            value: Valor a coercionar
            
        Returns:
            Valor coercionado al tipo apropiado
        """
        if value is None:
            return None
        
        if feature in self._numeric_defaults:
            return as_float(value)
        if feature in self._categorical_defaults:
            return as_string(value)
        
        return value

    def _get_default(self, feature: str) -> Any:
        """Obtiene el valor por defecto para una feature.
        
        Args:
            feature: Nombre de la feature
            
        Returns:
            Valor por defecto
            
        Raises:
            ValueError: Si la feature no tiene valor por defecto definido
        """
        if feature in self._numeric_defaults:
            return self._numeric_defaults[feature]
        if feature in self._categorical_defaults:
            return self._categorical_defaults[feature]
        
        raise ValueError(
            f"No hay datos ni valor por defecto para la feature requerida: {feature}"
        )