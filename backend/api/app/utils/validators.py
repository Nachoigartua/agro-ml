"""Validadores compartidos entre diferentes módulos."""
from __future__ import annotations

from typing import Set
from uuid import UUID


def validate_cultivo(cultivo: str, allowed_cultivos: Set[str]) -> str:
    """Valida y normaliza el nombre de un cultivo.
    
    Args:
        cultivo: Nombre del cultivo a validar
        allowed_cultivos: Set de cultivos permitidos
        
    Returns:
        Cultivo normalizado (lowercase)
        
    Raises:
        ValueError: Si el cultivo no está en la lista de permitidos
    """
    normalised = (cultivo or "").strip().lower()
    if normalised not in allowed_cultivos:
        allowed = ", ".join(sorted(allowed_cultivos))
        raise ValueError(f"cultivo debe ser uno de: {allowed}")
    return normalised


def validate_uuid_format(value: str, *, field: str = "value") -> None:
    """Valida que un string tenga formato UUID válido.
    
    Args:
        value: String a validar
        field: Nombre del campo para mensajes de error
        
    Raises:
        ValueError: Si el formato no es válido
    """
    try:
        UUID(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} debe tener formato UUID válido") from exc