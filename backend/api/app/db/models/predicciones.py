"""Model definition for table predicciones."""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.db.base import Base


class Prediccion(Base):
    """Registro de predicciones o recomendaciones generadas por modelos ML."""

    __tablename__ = "predicciones"

    id = sa.Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    lote_id = sa.Column(postgresql.UUID(as_uuid=True), nullable=False)
    cliente_id = sa.Column(postgresql.UUID(as_uuid=True), nullable=False)
    tipo_prediccion = sa.Column(sa.String(50), nullable=False)
    cultivo = sa.Column(sa.String(50), nullable=True)
    fecha_creacion = sa.Column(
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    fecha_validez_desde = sa.Column(sa.Date(), nullable=True)
    fecha_validez_hasta = sa.Column(sa.Date(), nullable=True)
    recomendacion_principal = sa.Column(postgresql.JSONB, nullable=True)
    alternativas = sa.Column(postgresql.JSONB, nullable=True)
    nivel_confianza = sa.Column(sa.Float, nullable=True)
    datos_entrada = sa.Column(postgresql.JSONB, nullable=True)
    modelo_version = sa.Column(sa.String(20), nullable=True)

    def __repr__(self) -> str:
        return f"Prediccion(id={self.id!r}, tipo={self.tipo_prediccion!r})"
