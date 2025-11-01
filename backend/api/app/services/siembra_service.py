"""Servicio simplificado de recomendaciones de siembra."""
from __future__ import annotations

import io
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import joblib
import pandas as pd

from ..clients.main_system_client import MainSystemAPIClient
from ..core.logging import get_logger
from ..db.persistence import PersistenceContext
from ..dto.siembra import (
    SiembraRecommendationResponse,
    SiembraRequest,
    RecomendacionPrincipalSiembra,
)
from ..exceptions import CampaignNotFoundError as ExternalCampaignNotFoundError
from .siembra_risk_analyzer import SiembraRiskAnalyzer


class SiembraRecommendationService:
    """Genera la fecha de siembra recomendada usando el modelo entrenado."""

    def __init__(
        self,
        main_system_client: MainSystemAPIClient,
        *,
        persistence_context: PersistenceContext,
        model_name: str = "modelo_siembra",
        model_type: str = "random_forest_regressor",
        risk_analyzer: Optional[SiembraRiskAnalyzer] = None,
        # ↑ Se agrega el analizador como dependencia opcional
    ) -> None:
        self.main_system_client = main_system_client
        self.logger = get_logger("siembra_service")
        self._risk_analyzer = risk_analyzer or SiembraRiskAnalyzer(logger=self.logger)
        self._persistence_context = persistence_context
        self._model_name = model_name
        self._model_type = model_type

        self._model = None
        self._preprocessor = None
        self._feature_order: list[str] = []
        self._numeric_defaults: Dict[str, float] = {}
        self._categorical_defaults: Dict[str, str] = {}
        self._model_metadata: Dict[str, Any] = {}
        self._model_loaded = False
        self._loaded_model_id: Optional[str] = None

    async def _ensure_model_loaded(self) -> None:
        if self._model_loaded:
            return

        entidad = await self._get_active_model()
        self._load_model_from_blob(entidad.archivo_modelo)
        self._loaded_model_id = str(entidad.id)
        self._model_metadata.setdefault("model_version", entidad.version)
        self._model_metadata.setdefault("version", entidad.version)
        self._model_metadata.setdefault("model_name", entidad.nombre)
        self.logger.info(
            "Modelo de siembra cargado desde base de datos (id=%s, version=%s).",
            self._loaded_model_id,
            entidad.version,
        )

        self._model_loaded = True

    async def _get_active_model(self):
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
                f"No se encontró un modelo activo en base de datos con nombre={self._model_name} y tipo={self._model_type}."
            )
        return entidad

    def _load_model_from_blob(self, blob: bytes) -> None:
        buffer = io.BytesIO(blob)
        model, preprocessor, metadata = joblib.load(buffer)
        self._apply_loaded_model(model, preprocessor, metadata)

    def _apply_loaded_model(self, model, preprocessor, metadata: Dict[str, Any] | None) -> None:
        self._model = model
        self._preprocessor = preprocessor

        self._model_metadata = metadata or {}
        self._feature_order = list(self._model_metadata.get("features", []))
        defaults = self._model_metadata.get("feature_defaults", {})
        self._numeric_defaults = {
            key: float(value) for key, value in defaults.get("numeric", {}).items()
        }
        self._categorical_defaults = {
            key: str(value) for key, value in defaults.get("categorical", {}).items()
        }

        if not self._feature_order:
            raise ValueError("El modelo cargado no contiene el orden de features esperado")

    async def generate_recommendation(
        self,
        request: SiembraRequest,
    ) -> SiembraRecommendationResponse:
        await self._ensure_model_loaded()

        lote_data = await self.main_system_client.get_lote_data(request.lote_id)
        feature_row = self._build_feature_row(lote_data)

        # Sobrescribir cultivo_anterior con el cultivo actual del request
        feature_row["cultivo_anterior"] = request.cultivo

        dataframe = pd.DataFrame([feature_row], columns=self._feature_order)
        transformed = self._preprocessor.transform(dataframe)
        predicted_day = self._predict_day_of_year(transformed)
        target_year = self._resolve_target_year_from_campaign(request)
        fecha_optima = self._day_of_year_to_date(predicted_day, target_year)

        ventana_inicio = fecha_optima - timedelta(days=2)
        ventana_fin = fecha_optima + timedelta(days=2)

        try:
              #se ejecuta el analizador de riesgos climático
            riesgos = await self._risk_analyzer.evaluate(
                lote_data,
                fecha_objetivo=fecha_optima,
                ventana=(ventana_inicio, ventana_fin),
            )
        except Exception:
            self.logger.exception("Error durante el analisis de riesgos de siembra", extra={"lote_id": request.lote_id})
            riesgos = [self._risk_analyzer.default_risk_message]
        
        ventana = [
            #Calcula las fechas en variables (ventana_inicio, ventana_fin), antes estaban inline (me parece mejor asi)
            ventana_inicio.strftime("%d-%m-%Y"),
            ventana_fin.strftime("%d-%m-%Y"),
        ]
        # se agregan los riesgos al modelo de respuesta
        recomendacion_principal = RecomendacionPrincipalSiembra(
            fecha_optima=fecha_optima.strftime("%d-%m-%Y"),
            ventana=ventana,
            confianza=1.0,
            riesgos=riesgos,
           
        )

        response = SiembraRecommendationResponse(
            lote_id=request.lote_id,
            tipo_recomendacion="siembra",
            recomendacion_principal=recomendacion_principal,
            alternativas=[],
            nivel_confianza=1.0,
            factores_considerados=[],
            costos_estimados={},
            fecha_generacion=datetime.now(timezone.utc),
            cultivo=request.cultivo,
        )

        await self._persist_recommendation(request, response)

        return response

    async def _persist_recommendation(
        self,
        request: SiembraRequest,
        response: SiembraRecommendationResponse,
    ) -> None:
        """Guarda la predicción generada, fallando si no hay repositorio disponible."""

        if self._persistence_context.predicciones is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con un repositorio de predicciones configurado."
            )

        ventana = response.recomendacion_principal.ventana
        fecha_validez_desde = None
        fecha_validez_hasta = None
        if len(ventana) == 2:
            try:
                fecha_validez_desde = datetime.strptime(ventana[0], "%d-%m-%Y").date()
                fecha_validez_hasta = datetime.strptime(ventana[1], "%d-%m-%Y").date()
            except ValueError:
                self.logger.warning("No se pudo parsear la ventana de la recomendación a fechas válidas.", extra={"ventana": ventana})

        await self._persistence_context.predicciones.save(
            lote_id=request.lote_id,
            cliente_id=request.cliente_id,
            tipo_prediccion=response.tipo_recomendacion,
            cultivo=response.cultivo,
            recomendacion_principal=response.recomendacion_principal.model_dump(mode="json"),
            alternativas=[dict(alt) for alt in response.alternativas],
            nivel_confianza=response.nivel_confianza,
            datos_entrada=request.model_dump(mode="json"),
            modelo_version=self._model_metadata.get("model_version") or self._model_metadata.get("version"),
            fecha_validez_desde=fecha_validez_desde,
            fecha_validez_hasta=fecha_validez_hasta,
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
        if feature.startswith("precipitacion_"):
            return self._as_float(clima.get(feature))
        if feature == "cultivo_anterior":
            return None  # se sobrescribe luego con el cultivo del request

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
        if day < 1 or day > 365:
            self.logger.warning(f"Predicción fuera de rango: {day} (valor original: {value})")
        return day

    def _resolve_target_year_from_campaign(self, request: SiembraRequest) -> int:
        """Determina el año objetivo desde `campana` dividiendo por '/'."""
        campana = (request.campana or "").strip()
        if not campana:
            raise ExternalCampaignNotFoundError(
                "El campo 'campana' es requerido y no llegó como correspondía"
            )

        partes = [p.strip() for p in campana.split("/")]
        if len(partes) < 2:
            raise ExternalCampaignNotFoundError(
                "El campo 'campana' es requerido y no llegó como correspondía"
            )

        anio_str = partes[1]
        if not re.fullmatch(r"(?:19|20)\d{2}", anio_str):
            raise ExternalCampaignNotFoundError(
                "El campo 'campana' es requerido y no llegó como correspondía"
            )

        return int(anio_str)

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
