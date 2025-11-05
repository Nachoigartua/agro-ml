"""Conversores de tipos para sanitización de datos."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID


def as_float(value: Any) -> Optional[float]:
    """Convierte un valor a float de forma segura.
    
    Args:
        value: Valor a convertir
        
    Returns:
        float si la conversión es exitosa, None en caso contrario
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_string(value: Any) -> Optional[str]:
    """Convierte un valor a string normalizado (lowercase, sin espacios).
    
    Args:
        value: Valor a convertir
        
    Returns:
        string normalizado si tiene contenido, None en caso contrario
    """
    if value is None:
        return None
    normalised = str(value).strip().lower()
    return normalised or None


def coerce_uuid(value: str | UUID, *, field: str = "value") -> UUID:
    """Convierte y valida que un valor sea un UUID válido.
    
    Args:
        value: Valor a convertir (string o UUID)
        field: Nombre del campo para mensajes de error
        
    Returns:
        UUID válido
        
    Raises:
        ValueError: Si el valor no es un UUID válido
    """
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} debe ser un UUID válido") from exc