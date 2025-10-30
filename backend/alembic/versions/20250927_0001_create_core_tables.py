"""create modelos_ml and predicciones tables"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "202509270001"
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "modelos_ml",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("tipo_modelo", sa.String(length=50), nullable=False),
        sa.Column("archivo_modelo", sa.LargeBinary(), nullable=False),
        sa.Column("metricas_performance", postgresql.JSONB(), nullable=True),
        sa.Column("fecha_entrenamiento", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_table(
        "predicciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_prediccion", sa.String(length=50), nullable=False),
        sa.Column("cultivo", sa.String(length=50), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("fecha_validez_desde", sa.Date(), nullable=True),
        sa.Column("fecha_validez_hasta", sa.Date(), nullable=True),
        sa.Column("recomendacion_principal", postgresql.JSONB(), nullable=True),
        sa.Column("alternativas", postgresql.JSONB(), nullable=True),
        sa.Column("nivel_confianza", sa.Float(), nullable=True),
        sa.Column("datos_entrada", postgresql.JSONB(), nullable=True),
        sa.Column("modelo_version", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("predicciones")
    op.drop_table("modelos_ml")
