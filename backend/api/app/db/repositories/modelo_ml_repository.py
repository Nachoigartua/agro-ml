"""Repository utilities for ModeloML entities."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.modelos_ml import ModeloML


class ModeloMLRepository:
    """Encapsula operaciones de persistencia para modelos de machine learning."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        nombre: str,
        version: str,
        tipo_modelo: str,
        archivo_modelo: bytes,
        metricas_performance: Mapping[str, Any] | None,
        fecha_entrenamiento: datetime,
        activo: bool = True,
    ) -> ModeloML:
        """Crea y persiste un registro de ``ModeloML`` devolviendo la entidad creada."""

        entidad = ModeloML(
            nombre=nombre,
            version=version,
            tipo_modelo=tipo_modelo,
            archivo_modelo=archivo_modelo,
            metricas_performance=dict(metricas_performance or {}),
            fecha_entrenamiento=fecha_entrenamiento,
            activo=activo,
        )
        self._session.add(entidad)
        await self._session.flush()
        return entidad

    async def get_active(
        self,
        *,
        nombre: str | None = None,
        tipo_modelo: str | None = None,
    ) -> ModeloML | None:
        """Recupera el último modelo activo filtrando opcionalmente por nombre/tipo."""

        stmt = select(ModeloML).where(ModeloML.activo.is_(True))
        if nombre:
            stmt = stmt.where(ModeloML.nombre == nombre)
        if tipo_modelo:
            stmt = stmt.where(ModeloML.tipo_modelo == tipo_modelo)
        stmt = stmt.order_by(ModeloML.fecha_entrenamiento.desc()).limit(1)

        resultado = await self._session.execute(stmt)
        return resultado.scalar_one_or_none()
