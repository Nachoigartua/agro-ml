"""Servicio para calcular nivel de confianza basado en métricas del modelo.

Dado un diccionario de ``metricas_performance`` (por ejemplo, del último
modelo activo), deriva un puntaje de confianza normalizado en [0, 1]. No
realiza accesos a base de datos; el llamador debe proveer las métricas.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from ..core.logging import get_logger


class ConfidenceService:
    """Calcula un score de confianza usando métricas de performance.

    Estrategia por defecto:
    - Usa ``r2`` tal cual (clamp 0..1).
    - Normaliza MAE y RMSE contra umbrales de referencia (en días) y los
      convierte a valores tipo precisión: ``1 - min(err/ref, 1)``.
    - Combina con pesos: r2=0.6, rmse=0.25, mae=0.15 (re-normalizando pesos
      si alguna métrica no está disponible).

    Umbrales por defecto (pensando en día-del-año):
    - ``mae_ref_days = 10``
    - ``rmse_ref_days = 15``
    """

    def __init__(
        self,
        *,
        mae_ref_days: float = 10.0,
        rmse_ref_days: float = 15.0,
    ) -> None:
        self._mae_ref = float(mae_ref_days)
        self._rmse_ref = float(rmse_ref_days)
        self._logger = get_logger("confidence_service")

    def score(
        self,
        metrics: Mapping[str, Any] | None,
        *,
        metadata: Optional[Mapping[str, Any]] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        cultivo: Optional[str] = None,
    ) -> float:
        """Calcula el score de confianza.

        - Si hay metadatos de clustering (``confidence_kmeans``) y coordenadas
          validas, usa primero metricas por zona y cultivo.
        - Caso contrario, cae en las metricas globales.

        Requisitos para el calculo: disponer de al menos una metrica utilizable
        (r2, rmse o mae) segun la fuente elegida.
        """
        zone_metrics = None
        if metadata is not None and lat is not None and lon is not None:
            try:
                zone_metrics = self._metrics_from_zone(metadata, lat, lon, cultivo)
            except Exception as exc:
                self._logger.warning(
                    "Fallo al calcular confianza por clustering, usando global.",
                    extra={"error": str(exc)},
                )
                zone_metrics = None

        if zone_metrics:
            return self._score_from_metrics(zone_metrics)

        if not metrics:
            raise RuntimeError(
                "No se encontraron métricas de performance del modelo para calcular confianza."
            )
        return self._score_from_metrics(metrics)

    def _metrics_from_zone(
        self,
        metadata: Mapping[str, Any],
        lat: float,
        lon: float,
        cultivo: Optional[str],
    ) -> Optional[Mapping[str, Any]]:
        info = metadata.get("confidence_kmeans") if isinstance(metadata, Mapping) else None
        if not isinstance(info, Mapping):
            return None
        centers = info.get("cluster_centers") or info.get("centers")
        if not isinstance(centers, list) or not centers:
            return None

        idx = _nearest_center(lat, lon, centers)
        if idx is None:
            return None

        crop_metrics_by_zone = info.get("zone_crop_metrics")
        if isinstance(crop_metrics_by_zone, Mapping) and cultivo:
            crop_key = str(cultivo).strip().lower()
            z = str(idx)
            zone_dict = crop_metrics_by_zone.get(z)
            if isinstance(zone_dict, Mapping):
                m = zone_dict.get(crop_key)
                if isinstance(m, Mapping) and m:
                    return m

        zone_metrics = info.get("zone_metrics")
        if isinstance(zone_metrics, Mapping):
            m = zone_metrics.get(str(idx))
            if isinstance(m, Mapping) and m:
                return m
        return None

    # ---------- combinación Global/Cluster/Dominio ----------
    def score_combined(
        self,
        metrics: Mapping[str, Any] | None,
        *,
        metadata: Optional[Mapping[str, Any]] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        cultivo: Optional[str] = None,
        features: Optional[Mapping[str, Any]] = None,
    ) -> float:
        """Devuelve confianza combinada: 0.25*Global + 0.40*Cluster + 0.35*Dominio."""
        if not metrics:
            raise RuntimeError(
                "No se encontraron métricas de performance del modelo para calcular confianza."
            )

        global_score = self._score_from_metrics(metrics)

        cluster_score = global_score
        if metadata is not None and lat is not None and lon is not None:
            try:
                zone_metrics = self._metrics_from_zone(metadata, lat, lon, cultivo)
                if zone_metrics:
                    cluster_score = self._score_from_metrics(zone_metrics)
            except Exception as exc:
                self._logger.warning(
                    "Fallo al calcular confianza por clustering, usando global.",
                    extra={"error": str(exc)},
                )

        domain_score = 1.0
        if metadata is not None and features is not None:
            try:
                s = self._domain_score(features, metadata)
                if s is not None:
                    domain_score = s
            except Exception as exc:
                self._logger.warning(
                    "Fallo al calcular dominio de features, ignorando penalización.",
                    extra={"error": str(exc)},
                )

        final = (0.25 * global_score) + (0.40 * cluster_score) + (0.35 * domain_score)
        return _clamp(final, 0.0, 1.0)

    # ---------- dominio basado en feature_stats ----------
    def _domain_score(
        self,
        features: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> Optional[float]:
        fs = metadata.get("feature_stats") if isinstance(metadata, Mapping) else None
        if not isinstance(fs, Mapping):
            return None

        scores: list[float] = []

        # numéricas
        num = fs.get("numeric")
        if isinstance(num, Mapping):
            for name, stats in num.items():
                if not isinstance(stats, Mapping):
                    continue
                v = features.get(name)
                if v is None:
                    continue
                try:
                    x = float(v)
                    lo = float(stats.get("min"))
                    hi = float(stats.get("max"))
                except Exception:
                    continue
                if lo > hi:
                    lo, hi = hi, lo
                if lo == hi:
                    scores.append(1.0 if x == lo else 0.0)
                    continue
                if lo <= x <= hi:
                    scores.append(1.0)
                else:
                    excedente = min(abs(x - lo), abs(x - hi))
                    rango = max(hi - lo, 1e-9)
                    s = 1.0 - _clamp(excedente / rango, 0.0, 1.0)
                    scores.append(s)

        # categóricas
        cat = fs.get("categorical")
        if isinstance(cat, Mapping):
            for name, stats in cat.items():
                if not isinstance(stats, Mapping):
                    continue
                vals = stats.get("values")
                if not isinstance(vals, list):
                    continue
                v = features.get(name)
                if v is None:
                    continue
                key = str(v).strip().lower()
                allowed = {str(x).strip().lower() for x in vals}
                scores.append(1.0 if key in allowed else 0.0)

        if not scores:
            return None
        return _clamp(sum(scores) / len(scores), 0.0, 1.0)

    # ---------- helpers ----------
    def _score_from_metrics(self, metrics: Mapping[str, Any]) -> float:
        r2 = _extract_float(metrics, "r2", "r_2", "r2_score")
        mae = _extract_float(metrics, "mae", "mean_absolute_error")
        rmse = _extract_float(metrics, "rmse", "root_mean_squared_error", "root_mse")

        components: list[tuple[float, float]] = []  # (value, weight)

        if r2 is not None:
            components.append((_clamp(r2, 0.0, 1.0), 0.60))
        if rmse is not None and self._rmse_ref > 0:
            rmse_norm = 1.0 - _clamp(rmse / self._rmse_ref, 0.0, 1.0)
            components.append((rmse_norm, 0.25))
        if mae is not None and self._mae_ref > 0:
            mae_norm = 1.0 - _clamp(mae / self._mae_ref, 0.0, 1.0)
            components.append((mae_norm, 0.15))

        if not components:
            # Sin métricas útiles: error explícito
            raise RuntimeError(
                "Las métricas no contienen valores utilizables (r2, rmse o mae)."
            )

        total_weight = sum(w for _, w in components)
        if total_weight <= 0:
            raise RuntimeError("No es posible combinar métricas: pesos totales inválidos.")

        weighted = sum(val * w for val, w in components) / total_weight
        return _clamp(weighted, 0.0, 1.0)


def _extract_float(metrics: Mapping[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        if key in metrics:
            try:
                return float(metrics[key])
            except (TypeError, ValueError):
                continue
        # probar con variantes de mayúsc/minúsc
        for k, v in metrics.items():
            if isinstance(k, str) and k.lower() == key.lower():
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
    return None


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _nearest_center(lat: float, lon: float, centers: list) -> Optional[int]:
    """Devuelve el indice del centroide mas cercano.

    Usa distancia euclidea simple en coordenadas (lat, lon).
    """
    try:
        best_idx = None
        best_d2 = None
        for i, c in enumerate(centers):
            if not isinstance(c, (list, tuple)) or len(c) < 2:
                continue
            dy = float(lat) - float(c[0])
            dx = float(lon) - float(c[1])
            d2 = dy * dy + dx * dx
            if best_d2 is None or d2 < best_d2:
                best_d2 = d2
                best_idx = i
        return best_idx
    except Exception:
        return None
