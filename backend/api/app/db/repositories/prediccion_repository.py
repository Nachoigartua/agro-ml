"""Repository utilities for Prediccion model."""
from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Any, Mapping, Sequence, Optional, Union

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.predicciones import Prediccion
from app.utils.type_converters import coerce_uuid


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
        cultivo: Optional[str] = None,
        recomendacion_principal: Optional[Mapping[str, Any]] = None,
        alternativas: Optional[Sequence[Mapping[str, Any]]] = None,
        nivel_confianza: Optional[float] = None,
        datos_entrada: Optional[Mapping[str, Any]] = None,
        modelo_version: Optional[str] = None,
        fecha_validez_desde: Optional[date] = None,
        fecha_validez_hasta: Optional[date] = None,
    ) -> Prediccion:
        """Crea y persiste una predicción, retornando la entidad almacenada."""

        entidad = Prediccion(
            lote_id=coerce_uuid(lote_id, field="lote_id"),
            cliente_id=coerce_uuid(cliente_id, field="cliente_id"),
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

    async def list_by_filters(
        self,
        *,
        tipo_prediccion: Optional[str] = None,
        cliente_id: Optional[Union[str, UUID]] = None,
        lote_id: Optional[Union[str, UUID]] = None,
        cultivo: Optional[str] = None,
        campana: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Prediccion]:
        """Recupera predicciones filtradas según los criterios admitidos."""

        query = (
            sa.select(Prediccion)
            .order_by(Prediccion.fecha_creacion.desc(), Prediccion.id.desc())
            .offset(offset)
            .limit(limit)
        )

        if tipo_prediccion:
            query = query.where(Prediccion.tipo_prediccion == tipo_prediccion)

        if cliente_id:
            query = query.where(
                Prediccion.cliente_id == coerce_uuid(cliente_id, field="cliente_id")
            )

        if lote_id:
            query = query.where(
                Prediccion.lote_id == coerce_uuid(lote_id, field="lote_id")
            )

        if cultivo:
            query = query.where(sa.func.lower(Prediccion.cultivo) == cultivo.lower())

        if campana:
            campana_field = Prediccion.datos_entrada["campana"].astext
            query = query.where(campana_field == campana)

        result = await self._session.execute(query)
        return list(result.scalars().all())