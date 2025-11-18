"""ORM models."""

# Import model modules so Alembic can discover them via Base.metadata
from .modelos_ml import ModeloML  # noqa: F401
from .predicciones import Prediccion  # noqa: F401
