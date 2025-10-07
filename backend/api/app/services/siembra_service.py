"""Servicio simplificado de recomendaciones de siembra."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd

from ..clients.main_system_client import MainSystemAPIClient
from ..core.logging import get_logger
from ..dto.siembra import (
    SiembraRecommendationDetail,
    SiembraRecommendationResponse,
    SiembraRequest,
)

BACKEND_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = Path(os.getenv("AGRO_ML_PROJECT_ROOT", str(BACKEND_DIR.parent))).resolve()
DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "machine-learning"
    / "models"
    / "modelo_siembra.joblib"
)


class SiembraRecommendationService:
    """Genera la fecha de siembra recomendada usando el modelo entrenado."""

    def __init__(
        self,
        main_system_client: MainSystemAPIClient,
        *,
        model_path: Optional[Path | str] = None,
    ) -> None:
        self.main_system_client = main_system_client
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.logger = get_logger("siembra_service")

        self._model = None
        self._preprocessor = None
        self._feature_order: list[str] = []
        self._numeric_defaults: Dict[str, float] = {}
        self._categorical_defaults: Dict[str, str] = {}

        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo de siembra no encontrado en {self.model_path}"
            )

        model, preprocessor, metadata = joblib.load(self.model_path)
        self._model = model
        self._preprocessor = preprocessor

        metadata = metadata or {}
        self._feature_order = list(metadata.get("features", []))
        defaults = metadata.get("feature_defaults", {})
        self._numeric_defaults = {
            key: float(value) for key, value in defaults.get("numeric", {}).items()
        }
        self._categorical_defaults = {
            key: str(value) for key, value in defaults.get("categorical", {}).items()
        }

        if not self._feature_order:
            raise ValueError("El modelo cargado no contiene el orden de features esperado")

    async def generate_recommendation(
        self, request: SiembraRequest
    ) -> SiembraRecommendationResponse:
        lote_data = await self.main_system_client.get_lote_data(request.lote_id)
        feature_row = self._build_feature_row(lote_data)

        dataframe = pd.DataFrame([feature_row], columns=self._feature_order)
        transformed = self._preprocessor.transform(dataframe)
        predicted_day = self._predict_day_of_year(transformed)
        target_year = self._resolve_target_year(request)
        fecha_optima = self._day_of_year_to_date(predicted_day, target_year)

        recomendacion = SiembraRecommendationDetail(
            cultivo=request.cultivo,
            fecha_siembra=fecha_optima,
        )

        return SiembraRecommendationResponse(
            lote_id=request.lote_id,
            recomendacion_principal=recomendacion,
        )

    def _build_feature_row(self, lote_data: Dict[str, Any]) -> Dict[str, Any]:
        row: Dict[str, Any] = {}
        for feature in self._feature_order:
            value = self._extract_feature_value(feature, lote_data)
            if value is None:
                value = self._default_for(feature)
            row[feature] = value
        return row

    def _extract_feature_value(
        self, feature: str, lote_data: Dict[str, Any]
    ) -> Optional[Any]:
        ubicacion = lote_data.get("ubicacion") or {}
        suelo = lote_data.get("suelo") or {}
        clima = lote_data.get("clima") or {}

        if feature == "latitud":
            return self._as_float(ubicacion.get("latitud"))
        if feature == "longitud":
            return self._as_float(ubicacion.get("longitud"))
        if feature == "tipo_suelo":
            return self._as_string(suelo.get("tipo_suelo"))
        if feature == "ph_suelo":
            return self._as_float(suelo.get("ph_suelo"))
        if feature == "materia_organica_pct":
            origen = suelo.get("materia_organica_pct") or suelo.get("materia_organica")
            return self._as_float(origen)
        if feature == "cultivo_anterior":
            return self._as_string(lote_data.get("cultivo_anterior"))

        if feature in lote_data:
            return self._coerce_feature_value(feature, lote_data[feature])
        if feature in clima:
            return self._coerce_feature_value(feature, clima[feature])
        return None

    def _coerce_feature_value(self, feature: str, value: Any) -> Optional[Any]:
        if value is None:
            return None
        if feature in self._numeric_defaults:
            return self._as_float(value)
        if feature in self._categorical_defaults:
            return self._as_string(value)
        return value

    def _default_for(self, feature: str) -> Any:
        if feature in self._numeric_defaults:
            return self._numeric_defaults[feature]
        if feature in self._categorical_defaults:
            return self._categorical_defaults[feature]
        raise ValueError(f"No hay datos para la feature requerida: {feature}")

    def _predict_day_of_year(self, transformed) -> int:
        prediction = float(self._model.predict(transformed)[0])
        return self._clamp_day_of_year(prediction)

    def _clamp_day_of_year(self, value: float) -> int:
        day = int(round(value))
        if day < 1:
            return 1
        if day > 366:
            return 366
        return day

    def _resolve_target_year(self, request: SiembraRequest) -> int:
        return request.fecha_consulta.year + 1

    @staticmethod
    def _day_of_year_to_date(day_of_year: int, year: int) -> datetime:
        start = datetime(year, 1, 1)
        return start + timedelta(days=day_of_year - 1)

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        normalised = str(value).strip().lower()
        return normalised or None
