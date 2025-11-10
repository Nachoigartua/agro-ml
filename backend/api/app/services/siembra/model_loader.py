"""Carga y gestión de modelos de Machine Learning."""
from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple

import joblib

from ...core.logging import get_logger
from ...db.persistence import PersistenceContext


logger = get_logger("siembra.model_loader")


class ModelLoader:
    """Responsable de cargar y gestionar modelos ML desde la base de datos."""

    def __init__(
        self,
        persistence_context: PersistenceContext,
        model_name: str = "modelo_siembra",
        model_type: str = "random_forest_regressor",
    ):
        """Inicializa el cargador de modelos.
        
        Args:
            persistence_context: Contexto de persistencia con acceso a repositorios
            model_name: Nombre del modelo a cargar
            model_type: Tipo de modelo (ej: random_forest_regressor)
        """
        self._persistence_context = persistence_context
        self._model_name = model_name
        self._model_type = model_type
        
        self._model = None
        self._preprocessor = None
        self._metadata: Dict[str, Any] = {}
        self._performance_metrics: Dict[str, Any] = {}
        self._loaded_model_id: Optional[str] = None
        self._is_loaded = False

    async def load(self) -> None:
        """Carga el modelo activo desde la base de datos.
        
        Raises:
            RuntimeError: Si no hay repositorio configurado o no hay modelo activo
        """
        if self._is_loaded:
            logger.debug("Modelo ya cargado, omitiendo carga")
            return

        entidad = await self._get_active_model()
        model, preprocessor, metadata = self._deserialize_model(entidad.archivo_modelo)
        
        self._model = model
        self._preprocessor = preprocessor
        self._metadata = metadata or {}
        self._loaded_model_id = str(entidad.id)
        # Guardar métricas de performance desde la entidad (JSONB)
        try:
            self._performance_metrics = dict(entidad.metricas_performance or {})
        except Exception:
            self._performance_metrics = {}
        
        # Asegurar que version esté presente
        if "model_version" not in self._metadata:
            self._metadata["model_version"] = entidad.version
        if "version" not in self._metadata:
            self._metadata["version"] = entidad.version
        if "model_name" not in self._metadata:
            self._metadata["model_name"] = entidad.nombre
        
        self._is_loaded = True
        
        logger.info(
            "Modelo cargado exitosamente",
            extra={
                "model_id": self._loaded_model_id,
                "version": entidad.version,
                "name": entidad.nombre,
            }
        )

    async def _get_active_model(self):
        """Obtiene el modelo activo desde el repositorio."""
        if self._persistence_context.modelos is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con repositorio de modelos configurado."
            )

        entidad = await self._persistence_context.modelos.get_active(
            nombre=self._model_name,
            tipo_modelo=self._model_type,
        )
        
        if entidad is None:
            raise RuntimeError(
                f"No se encontró un modelo activo con nombre={self._model_name} "
                f"y tipo={self._model_type}."
            )
        
        return entidad

    @staticmethod
    def _deserialize_model(blob: bytes) -> Tuple[Any, Any, Dict[str, Any]]:
        """Deserializa el modelo desde bytes.
        
        Args:
            blob: Bytes del modelo serializado
            
        Returns:
            Tupla de (modelo, preprocessor, metadata)
        """
        buffer = io.BytesIO(blob)
        return joblib.load(buffer)

    @property
    def model(self):
        """Retorna el modelo cargado."""
        self._ensure_loaded()
        return self._model

    @property
    def preprocessor(self):
        """Retorna el preprocessor cargado."""
        self._ensure_loaded()
        return self._preprocessor

    @property
    def metadata(self) -> Dict[str, Any]:
        """Retorna los metadatos del modelo."""
        self._ensure_loaded()
        return self._metadata

    @property
    def performance_metrics(self) -> Dict[str, Any]:
        """Retorna el diccionario de métricas de performance (JSONB)."""
        self._ensure_loaded()
        return self._performance_metrics

    @property
    def feature_order(self) -> list[str]:
        """Retorna el orden de features esperado por el modelo."""
        return list(self.metadata.get("features", []))

    @property
    def feature_defaults(self) -> Dict[str, Any]:
        """Retorna los valores por defecto de las features."""
        return self.metadata.get("feature_defaults", {})

    def _ensure_loaded(self) -> None:
        """Verifica que el modelo esté cargado."""
        if not self._is_loaded:
            raise RuntimeError(
                "El modelo no ha sido cargado. Llame a load() antes de usar el modelo."
            )
