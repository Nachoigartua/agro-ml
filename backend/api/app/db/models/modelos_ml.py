"""Model definition for table modelos_ml."""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.db.base import Base


class ModeloML(Base):
    """Representa un modelo de machine learning almacenado en base de datos."""

    __tablename__ = "modelos_ml"

    id = sa.Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    nombre = sa.Column(sa.String(100), nullable=False)
    version = sa.Column(sa.String(20), nullable=False)
    tipo_modelo = sa.Column(sa.String(50), nullable=False)
    archivo_modelo = sa.Column(sa.LargeBinary, nullable=False)
    metricas_performance = sa.Column(postgresql.JSONB, nullable=True)
    fecha_entrenamiento = sa.Column(sa.DateTime(timezone=True), nullable=True)
    activo = sa.Column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    def __repr__(self) -> str:
        return f"ModeloML(id={self.id!r}, nombre={self.nombre!r}, version={self.version!r})"
