"""
Validation utilities
"""
from typing import Any, Dict
from datetime import date, datetime


def validate_date_range(fecha_desde: date, fecha_hasta: date) -> bool:
    """Validate that fecha_hasta is after fecha_desde"""
    return fecha_hasta >= fecha_desde


def validate_coordinates(latitud: float, longitud: float) -> bool:
    """Validate geographic coordinates"""
    return -90 <= latitud <= 90 and -180 <= longitud <= 180


def validate_cultivo(cultivo: str) -> bool:
    """Validate cultivo type"""
    cultivos_validos = ["trigo", "soja", "maiz", "cebada", "girasol"]
    return cultivo.lower() in cultivos_validos


def validate_positive_number(value: float) -> bool:
    """Validate that a number is positive"""
    return value > 0


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize input data"""
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Remove leading/trailing whitespace
            sanitized[key] = value.strip()
        else:
            sanitized[key] = value
    
    return sanitized