"""Servicio de recomendaciones de siembra respaldado por datos reales."""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from pydantic import ValidationError

try:  # pragma: no cover - soporta entornos sin redis instalado
    from redis.asyncio import Redis  # type: ignore
    from redis.exceptions import RedisError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Redis = None  # type: ignore

    class RedisError(Exception):
        """Excepcion local usada cuando redis no esta disponible."""

from ..clients.main_system_client import MainSystemAPIClient
from ..core.logging import get_logger
from ..dto.siembra import (
    RecomendacionBase,
    SiembraRecommendationResponse,
    SiembraRequest,
)

DEFAULT_CACHE_TTL_SECONDS = 6 * 3600
BACKEND_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = Path(os.getenv("AGRO_ML_PROJECT_ROOT", str(BACKEND_DIR.parent))).resolve()
DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "machine-learning"
    / "models"
    / "modelo_siembra.joblib"
)
DATASET_PATH = PROJECT_ROOT / "data" / "dataset_completo_argentina.csv"

class SiembraParametersCalculator:
    """Calcula parámetros técnicos de siembra basados en condiciones específicas."""
    
    def __init__(self):
        # Rangos base por cultivo (mínimos y máximos sugeridos)
        self._base_params = {
            "trigo": {"densidad": (120.0, 180.0), "profundidad": (2.0, 4.0), "espaciamiento": (15.0, 20.0)},
            "soja": {"densidad": (45.0, 75.0), "profundidad": (3.0, 5.0), "espaciamiento": (35.0, 70.0)},
            "maiz": {"densidad": (20.0, 30.0), "profundidad": (3.0, 7.0), "espaciamiento": (50.0, 80.0)},
            "cebada": {"densidad": (100.0, 140.0), "profundidad": (2.5, 3.5), "espaciamiento": (15.0, 20.0)}
        }

    def calculate_parameters(self, 
                           cultivo: str,
                           suelo: dict,
                           clima: dict,
                           ubicacion: dict) -> dict:
        """Calcula parámetros técnicos basados en condiciones específicas."""
        
        # 1. Obtener rango base
        base_range = self._base_params.get(cultivo.lower())
        if not base_range:
            raise ValueError(f"Cultivo no soportado: {cultivo}")

        # 2. Ajustar por tipo de suelo
        tipo_suelo = suelo.get("tipo_suelo", "").lower()
        densidad_adj = 1.0
        profundidad_adj = 1.0
        
        if tipo_suelo == "argiudol":
            densidad_adj *= 1.1  # Mejor suelo = mayor densidad
        elif tipo_suelo == "franco arenoso":
            densidad_adj *= 0.9
            profundidad_adj *= 1.2  # Suelo suelto = más profundidad

        # 3. Ajustar por materia orgánica
        mo = float(suelo.get("materia_organica", 0))
        if mo > 3.0:
            densidad_adj *= 1.05
        elif mo < 2.0:
            densidad_adj *= 0.95

        # 4. Ajustar por clima
        precip_media = sum([
            float(clima.get(f"precipitacion_{mes}", 0))
            for mes in ["marzo", "abril", "mayo"]
        ]) / 3

        if precip_media < 50:  # mm/mes
            densidad_adj *= 0.9
            profundidad_adj *= 1.1

        # 5. Calcular valores finales (promedio del rango * ajustes)
        densidad = (base_range["densidad"][0] + base_range["densidad"][1]) / 2 * densidad_adj
        profundidad = (base_range["profundidad"][0] + base_range["profundidad"][1]) / 2 * profundidad_adj
        espaciamiento = (base_range["espaciamiento"][0] + base_range["espaciamiento"][1]) / 2

        return {
            "densidad": round(densidad, 1),
            "profundidad": round(profundidad, 1),
            "espaciamiento": round(espaciamiento, 1)
        }

COSTOS_BASE: Dict[str, Dict[str, float]] = {
    "trigo": {"semilla": 135.0, "laboreo": 65.0},
    "soja": {"semilla": 95.0, "laboreo": 55.0},
    "maiz": {"semilla": 180.0, "laboreo": 75.0},
    "cebada": {"semilla": 120.0, "laboreo": 60.0},
}


class SiembraRecommendationService:
    """Genera recomendaciones de siembra apoyandose en el modelo entrenado."""

    def __init__(
        self,
        main_system_client: MainSystemAPIClient,
        *,
        model_path: Optional[Path | str] = None,
        redis_client: Optional[Any] = None,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    ) -> None:
        self.main_system_client = main_system_client
        self.redis_client = redis_client if (Redis is not None and redis_client) else None
        self.cache_ttl_seconds = cache_ttl_seconds
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.logger = get_logger("siembra_service")

        self._model = None
        self._preprocessor = None
        self._metadata: Dict[str, Any] = {}
        self._feature_order: list[str] = []
        self._numeric_defaults: Dict[str, float] = {}
        self._categorical_defaults: Dict[str, str] = {}
        self._reference_dataset = pd.DataFrame()

        self._load_model()
        self._load_reference_dataset()

    def _load_model(self) -> None:
        """Carga el modelo y el preprocesador serializados desde disco."""

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo de siembra no encontrado en {self.model_path}"
            )

        model, preprocessor, metadata = joblib.load(self.model_path)
        self._model = model
        self._preprocessor = preprocessor
        self._metadata = metadata or {}
        self._feature_order = list(self._metadata.get("features", []))

        defaults = self._metadata.get("feature_defaults", {})
        self._numeric_defaults = {
            key: float(value) for key, value in defaults.get("numeric", {}).items()
        }
        self._categorical_defaults = {
            key: str(value) for key, value in defaults.get("categorical", {}).items()
        }

        if not self._feature_order:
            raise ValueError("El modelo cargado no contiene el orden de features esperado")

    def _load_reference_dataset(self) -> None:
        """Carga el dataset real para derivar datos climaticos de referencia."""

        if not DATASET_PATH.exists():
            raise FileNotFoundError(
                f"Dataset de referencia no encontrado en {DATASET_PATH}"
            )

        df = pd.read_csv(DATASET_PATH)
        df["tipo_suelo"] = df["tipo_suelo"].astype(str).str.strip().str.lower()
        df["cultivo_anterior"] = df["cultivo_anterior"].astype(str).str.strip().str.lower()
        df = self._ensure_target_column(df)
        self._reference_dataset = df

    @staticmethod
    def _ensure_target_column(df: pd.DataFrame) -> pd.DataFrame:
        """Garantiza que la referencia tenga el objetivo derivado de fechas reales."""

        if "dia_del_ano" in df.columns:
            valores = df["dia_del_ano"].dropna()
            if not valores.empty and not valores.between(1, 366).all():
                raise ValueError("Los valores de dia_del_ano en el dataset de referencia no son validos")
            return df

        fecha_col = "fecha_siembra_estimada"
        if fecha_col not in df.columns:
            raise ValueError("El dataset de referencia debe tener fecha_siembra_estimada para derivar dia_del_ano")

        fechas = pd.to_datetime(df[fecha_col], errors='coerce', utc=False)
        if fechas.isna().any():
            raise ValueError("No se pudo convertir fecha_siembra_estimada a fechas validas en el dataset de referencia")

        df["dia_del_ano"] = fechas.dt.dayofyear.astype(int)
        return df

    async def generate_recommendation(
        self, request: SiembraRequest
    ) -> SiembraRecommendationResponse:
        """Genera una recomendacion de siembra para un lote especifico."""

        cache_key = self._build_cache_key(request)
        cached = await self._fetch_cached_response(cache_key)
        if cached:
            self.logger.info(
                "siembra_cache_hit",
                lote_id=str(request.lote_id),
                cultivo=request.cultivo,
            )
            return cached

        lote_data = await self.main_system_client.get_lote_data(request.lote_id)
        features, referencia, distancia = self._build_feature_vector(lote_data)

        dataframe = pd.DataFrame([features], columns=self._feature_order)
        transformed = self._preprocessor.transform(dataframe)
        prediccion = float(self._model.predict(transformed)[0])
        predicted_day = self._normalise_predicted_day(prediccion)
        target_year = self._resolve_target_year(request)
        fecha_optima = self._day_of_year_to_datetime(
            predicted_day, target_year=target_year
        )

        confianza = self._compute_confidence(distancia)
        parametros = self._get_recommendation_defaults(request.cultivo)
        costos = self._estimate_costs(request.cultivo)

        recomendacion_principal = RecomendacionBase(
            cultivo=request.cultivo,
            fecha_siembra=fecha_optima,
            densidad_siembra=parametros["densidad"],
            profundidad_siembra=parametros["profundidad"],
            espaciamiento_hileras=parametros["espaciamiento"],
            score=confianza,
        )

        alternativas = self._build_alternatives(
            fecha_optima,
            request.cultivo,
            parametros,
            confianza,
        )

        response = SiembraRecommendationResponse(
            lote_id=request.lote_id,
            tipo_recomendacion="siembra",
            recomendacion_principal=recomendacion_principal,
            alternativas=alternativas,
            nivel_confianza=confianza,
            factores_considerados=self._build_factores_considerados(referencia),
            costos_estimados=costos,
            fecha_generacion=datetime.utcnow(),
        )

        await self._store_cache_value(cache_key, response)

        self.logger.info(
            "siembra_prediction_generated",
            lote_id=str(request.lote_id),
            cultivo=request.cultivo,
            campana=request.campana,
            predicted_day=predicted_day,
            fecha_optima=fecha_optima.isoformat(),
            confianza=confianza,
        )
        return response

    def _build_feature_vector(
        self, lote: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], pd.Series, float]:
        """Arma el vector de features combinando datos del lote y del dataset real."""

        ubicacion = lote.get("ubicacion") or {}
        if "latitud" not in ubicacion or "longitud" not in ubicacion:
            raise ValueError("El lote no posee coordenadas registradas")

        latitud = float(ubicacion["latitud"])
        longitud = float(ubicacion["longitud"])
        referencia, distancia = self._find_reference_row(latitud, longitud)
        suelo = lote.get("suelo") or {}

        feature_values: Dict[str, Any] = {
            "latitud": latitud,
            "longitud": longitud,
            "temp_media_marzo": float(referencia["temp_media_marzo"]),
            "temp_media_abril": float(referencia["temp_media_abril"]),
            "temp_media_mayo": float(referencia["temp_media_mayo"]),
            "precipitacion_marzo": float(referencia["precipitacion_marzo"]),
            "precipitacion_abril": float(referencia["precipitacion_abril"]),
            "precipitacion_mayo": float(referencia["precipitacion_mayo"]),
            "tipo_suelo": str(suelo.get("tipo_suelo") or referencia["tipo_suelo"]),
            "ph_suelo": self._get_numeric_value(suelo.get("ph_suelo"), "ph_suelo"),
            "materia_organica_pct": self._get_numeric_value(
                suelo.get("materia_organica") or suelo.get("materia_organica_pct"),
                "materia_organica_pct",
            ),
            "cultivo_anterior": str(
                lote.get("cultivo_anterior") or referencia["cultivo_anterior"]
            ).lower(),
        }

        missing = [name for name in self._feature_order if name not in feature_values]
        if missing:
            raise ValueError(f"Faltan valores para las features: {', '.join(missing)}")

        # Guardar datos del lote actual para cálculos posteriores
        self._ultimo_suelo = suelo
        self._ultimo_clima = {
            k: feature_values[k] 
            for k in feature_values 
            if 'temp_' in k or 'precipitacion_' in k
        }
        self._ultima_ubicacion = {
            'latitud': latitud,
            'longitud': longitud
        }

        ordered_vector = {name: feature_values[name] for name in self._feature_order}
        return ordered_vector, referencia, distancia

    def _find_reference_row(self, latitud: float, longitud: float) -> Tuple[pd.Series, float]:
        """Busca el registro del dataset real mas cercano geograficamente."""

        if self._reference_dataset.empty:
            raise ValueError("El dataset de referencia se cargo vacio")

        coords = self._reference_dataset[["latitud", "longitud"]].to_numpy(dtype=float)
        objetivo = np.array([latitud, longitud], dtype=float)
        distancias = np.linalg.norm(coords - objetivo, axis=1)
        indice = int(distancias.argmin())
        return self._reference_dataset.iloc[indice], float(distancias[indice])

    def _get_numeric_value(self, value: Any, feature_name: str) -> float:
        """Devuelve el valor numerico para una feature con fallback a promedios reales."""

        if value is None:
            if feature_name not in self._numeric_defaults:
                raise ValueError(f"No hay valor por defecto para {feature_name}")
            return float(self._numeric_defaults[feature_name])
        return float(value)

    def _build_factores_considerados(self, referencia: pd.Series) -> list[str]:
        """Genera la lista de factores considerados para la respuesta."""

        provincia = str(referencia.get("provincia", "desconocida")).lower()
        return [
            f"clima_referencia:{provincia}",
            "cultivo_anterior",
            "suelo_lote",
            "modelo_random_forest",
        ]

    def _build_alternatives(
        self,
        base_date: datetime,
        cultivo: str,
        parametros: Dict[str, float],
        confianza: float,
    ) -> list[RecomendacionBase]:
        """Genera dos alternativas desplazando la fecha optima."""

        opciones = [(-10, 0.08), (10, 0.1)]
        alternativas: list[RecomendacionBase] = []
        for dias, penalizacion in opciones:
            alternativa = RecomendacionBase(
                cultivo=cultivo,
                fecha_siembra=base_date + timedelta(days=dias),
                densidad_siembra=parametros["densidad"],
                profundidad_siembra=parametros["profundidad"],
                espaciamiento_hileras=parametros["espaciamiento"],
                score=max(confianza - penalizacion, 0.5),
            )
            alternativas.append(alternativa)
        return alternativas

    def _normalise_predicted_day(self, value: float) -> int:
        """Limita la prediccion del modelo al rango valido del calendario."""

        return max(1, min(365, int(round(value))))

    def _day_of_year_to_datetime(self, day_of_year: int, *, target_year: int) -> datetime:
        """Convierte un numero de dia del anio a fecha calendario del anio objetivo."""

        base_year_start = datetime(target_year, 1, 1)
        return base_year_start + timedelta(days=day_of_year - 1)

    def _build_cache_key(self, request: SiembraRequest) -> str:
        """Arma una clave deterministica para reutilizar predicciones en cache."""

        return "siembra:{lote}:{cultivo}:{campana}:{consulta}".format(
            lote=str(request.lote_id),
            cultivo=request.cultivo,
            campana=request.campana,
            consulta=request.fecha_consulta.date().isoformat(),
        )

    async def _fetch_cached_response(
        self, cache_key: str
    ) -> Optional[SiembraRecommendationResponse]:
        """Obtiene resultados cacheados, ignorando errores de redis."""

        if not self.redis_client:
            return None

        try:
            payload = await self.redis_client.get(cache_key)
            if not payload:
                return None
            return SiembraRecommendationResponse.model_validate_json(payload)
        except (RedisError, ValidationError) as exc:
            self.logger.warning(
                "siembra_cache_fetch_failed",
                error=str(exc),
                cache_key=cache_key,
            )
            return None

    async def _store_cache_value(
        self, cache_key: str, response: SiembraRecommendationResponse
    ) -> None:
        """Guarda la respuesta en cache si hay redis disponible."""

        if not self.redis_client:
            return

        try:
            payload = response.model_dump_json()
            await self.redis_client.setex(cache_key, self.cache_ttl_seconds, payload)
        except (RedisError, TypeError) as exc:  # pragma: no cover - cache fallback
            self.logger.warning(
                "siembra_cache_store_failed",
                error=str(exc),
                cache_key=cache_key,
            )

    def _resolve_target_year(self, request: SiembraRequest) -> int:
        """Determina el anio calendario de la campaña siguiente."""

        matches = re.findall(r"\d{4}", request.campana or "")
        if len(matches) >= 2:
            candidate = int(matches[1])
        elif len(matches) == 1:
            candidate = int(matches[0]) + 1
        else:
            candidate = request.fecha_consulta.year + 1

        if candidate <= request.fecha_consulta.year:
            candidate = request.fecha_consulta.year + 1
        return candidate

    def _get_recommendation_defaults(self, cultivo: str, **kwargs) -> Dict[str, float]:
        """Calcula parámetros agronómicos según condiciones específicas."""
        calculator = SiembraParametersCalculator()
        
        # Obtener datos del último lote procesado (si existen)
        suelo = getattr(self, '_ultimo_suelo', {})
        clima = getattr(self, '_ultimo_clima', {})
        ubicacion = getattr(self, '_ultima_ubicacion', {})
        
        return calculator.calculate_parameters(
            cultivo=cultivo,
            suelo=suelo,
            clima=clima,
            ubicacion=ubicacion
        )

    def _estimate_costs(self, cultivo: str) -> Dict[str, float]:
        """Calcula costos estimados en base al cultivo objetivo."""

        cultivo_clave = cultivo.lower()
        return COSTOS_BASE.get(cultivo_clave, {"semilla": 110.0, "laboreo": 60.0})

    def _compute_confidence(self, distancia: float) -> float:
        """Deriva un nivel de confianza a partir de la distancia al punto de referencia."""

        distancia_km = distancia * 111.0
        return float(max(0.55, min(0.95, 0.95 - distancia_km / 400.0)))
