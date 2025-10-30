"""Repository utilities for Prediccion model."""
from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Any, Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.predicciones import Prediccion


class PrediccionRepository:
    """Encapsula operaciones de persistencia para predicciones."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        lote_id: str,
        cliente_id: str,
        tipo_prediccion: str,
        cultivo: str | None = None,
        recomendacion_principal: Mapping[str, Any] | None = None,
        alternativas: Sequence[Mapping[str, Any]] | None = None,
        nivel_confianza: float | None = None,
        datos_entrada: Mapping[str, Any] | None = None,
        modelo_version: str | None = None,
        fecha_validez_desde: date | None = None,
        fecha_validez_hasta: date | None = None,
    ) -> Prediccion:
        """Crea y persiste una predicción, retornando la entidad almacenada."""

        entidad = Prediccion(
            lote_id=self._coerce_uuid(lote_id, field="lote_id"),
            cliente_id=self._coerce_uuid(cliente_id, field="cliente_id"),
            tipo_prediccion=tipo_prediccion,
            cultivo=cultivo,
            recomendacion_principal=dict(recomendacion_principal or {}),
            alternativas=list(alternativas or []),
            nivel_confianza=nivel_confianza,
            datos_entrada=dict(datos_entrada or {}),
            modelo_version=modelo_version,
            fecha_validez_desde=fecha_validez_desde,
            fecha_validez_hasta=fecha_validez_hasta,
        )
        self._session.add(entidad)
        await self._session.flush()
        return entidad

    @staticmethod
    def _coerce_uuid(value: str | UUID, *, field: str) -> UUID:
        """Validates that the provided value is a valid UUID."""

        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{field} debe ser un UUID válido") from exc
