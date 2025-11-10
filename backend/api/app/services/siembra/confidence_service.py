"""Servicio para estimar nivel de confianza de una recomendación de siembra.

Combina 3 fuentes (ponderadas):
- Métricas generales del modelo (R2/RMSE)
- Métricas del cluster geográfico (R2/RMSE)
- Feature stats por rangos min/max (detección OOD)

Las métricas de clustering y feature_stats se esperan en el JSON de
`metricas_performance` del modelo activo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import math

from ...core.logging import get_logger


logger = get_logger("siembra.confidence_service")


@dataclass
class ConfidenceWeights:
    general: float = 0.25
    clustering: float = 0.40
    feature_stats: float = 0.35

    def normalised(self) -> "ConfidenceWeights":
        total = self.general + self.clustering + self.feature_stats
        if total <= 0:
            return ConfidenceWeights(1.0, 0.0, 0.0)
        return ConfidenceWeights(
            general=self.general / total,
            clustering=self.clustering / total,
            feature_stats=self.feature_stats / total,
        )


class ConfidenceEstimator:
    """Calcula nivel de confianza usando métricas y clustering guardados."""

    def __init__(
        self,
        *,
        performance_metrics: Dict[str, Any],
        weights: Optional[ConfidenceWeights] = None,
    ) -> None:
        self._metrics = performance_metrics or {}
        self._weights = (weights or ConfidenceWeights()).normalised()

    def compute(
        self,
        *,
        feature_row: Dict[str, Any],
        cultivo: Optional[str] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """Devuelve (confianza, detalles) con ponderación fija.

        details incluye cluster asignado, fuentes y parciales.
        """
        gen_score = self._score_general()
        cl_score, cl_details = self._score_clustering(feature_row, cultivo)
        fs_score, fs_details = self._score_feature_stats(feature_row)

        w = self._weights
        confidence = (
            w.general * gen_score + w.clustering * cl_score + w.feature_stats * fs_score
        )
        confidence = max(0.0, min(1.0, float(confidence)))

        details = {
            "general_score": gen_score,
            "clustering_score": cl_score,
            "feature_stats_score": fs_score,
            "clustering": cl_details,
            "feature_stats": fs_details,
            "weights": {
                "general": w.general,
                "clustering": w.clustering,
                "feature_stats": w.feature_stats,
            },
        }
        return confidence, details

    # --- Helpers de mapeo de métricas -> [0,1] ---
    def _conf_from_metrics(self, metrics: Dict[str, Any], target_range: Tuple[float, float]) -> float:
        """Convierte métricas (r2, rmse) a una confianza [0,1]."""
        if not isinstance(metrics, dict):
            return 0.5
        r2 = metrics.get("r2")
        if isinstance(r2, (int, float)) and math.isfinite(r2):
            # R2 típico en [0,1], clip por seguridad
            return float(max(0.0, min(1.0, r2)))
        rmse = metrics.get("rmse")
        if isinstance(rmse, (int, float)) and math.isfinite(rmse):
            rng = max(1e-6, target_range[1] - target_range[0])
            conf = 1.0 - min(float(rmse) / rng, 1.0)
            return max(0.0, min(1.0, conf))
        return 0.5

    def _target_range(self) -> Tuple[float, float]:
        fr = (
            self._metrics.get("feature_stats", {})
            .get("target_range", {})
        )
        tmin = fr.get("min", 1.0)
        tmax = fr.get("max", 366.0)
        return float(tmin), float(tmax)

    def _score_general(self) -> float:
        general = self._metrics.get("general", {})
        # Revertido: no usar probabilidad "±N días"; usar R2/RMSE únicamente
        return self._conf_from_metrics(general, self._target_range())

    def _nearest_centroid(self, lat: float, lon: float) -> Tuple[Optional[int], float]:
        clustering = self._metrics.get("clustering", {})
        cents = clustering.get("centroids") or []
        if not cents:
            return None, float("nan")
        best_idx = None
        best_dist = float("inf")
        for idx, (clat, clon) in enumerate(cents):
            try:
                d = (float(lat) - float(clat)) ** 2 + (float(lon) - float(clon)) ** 2
            except Exception:
                continue
            if d < best_dist:
                best_dist = d
                best_idx = idx
        return best_idx, math.sqrt(best_dist) if math.isfinite(best_dist) else float("nan")

    def _score_clustering(
        self, feature_row: Dict[str, Any], cultivo: Optional[str]
    ) -> Tuple[float, Dict[str, Any]]:
        cl = self._metrics.get("clustering", {})
        clusters = cl.get("clusters") or {}
        lat = feature_row.get("latitud")
        lon = feature_row.get("longitud")
        cid, dist = self._nearest_centroid(lat, lon)

        details = {"selected_cluster": cid, "distance": dist}
        if cid is None:
            return self._score_general(), details

        cluster_data = clusters.get(str(cid)) or {}
        target_range = self._target_range()
        general_fallback = self._score_general()

        # Preferir métricas por cultivo si existen (R2/RMSE)
        score = None
        if cultivo:
            by_crop = cluster_data.get("by_crop") or {}
            crop_metrics = by_crop.get(str(cultivo).lower())
            if crop_metrics:
                score = self._conf_from_metrics(crop_metrics, target_range)
                details["used"] = {"type": "by_crop", "crop": str(cultivo).lower()}

        size_used: Optional[int] = None
        if score is None:
            overall = cluster_data.get("overall") or {}
            score = self._conf_from_metrics(overall, target_range)
            details["used"] = {"type": "overall"}
            try:
                size_used = int(cluster_data.get("size"))
            except Exception:
                size_used = None
        # Si usamos por cultivo e incluye size, capturarlo
        if details.get("used", {}).get("type") == "by_crop":
            try:
                by_crop = cluster_data.get("by_crop") or {}
                cm = by_crop.get(str(cultivo).lower()) or {}
                size_used = int(cm.get("size"))
            except Exception:
                pass

        # Revertido: sin suavizado por tamaño de muestra ni silhouette
        return float(score if score is not None else general_fallback), details

    def _score_feature_stats(self, feature_row: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        fs = self._metrics.get("feature_stats", {})
        ranges = fs.get("numeric_ranges") or {}
        if not ranges:
            return 1.0, {"reason": "no_feature_stats"}

        deviations: List[Tuple[str, float]] = []
        total_dev = 0.0
        count = 0
        for fname, rr in ranges.items():
            try:
                v = float(feature_row.get(fname))
            except Exception:
                continue
            # Revertido: usar solo min/max
            fmin = float(rr.get("min", v))
            fmax = float(rr.get("max", v))
            frng = max(1e-9, fmax - fmin)
            dev = 0.0
            if v < fmin:
                dev = (fmin - v) / frng
            elif v > fmax:
                dev = (v - fmax) / frng
            dev = float(max(0.0, dev))
            deviations.append((fname, dev))
            total_dev += dev
            count += 1

        avg_dev = (total_dev / count) if count > 0 else 0.0
        # Penalización lineal hasta 1.0 fuera de rango (cap a 1.0)
        score = 1.0 - min(1.0, avg_dev)
        score = max(0.0, min(1.0, score))

        details = {
            "avg_deviation": avg_dev,
            "per_feature": [{"feature": n, "dev": d} for n, d in deviations if d > 0],
        }
        return score, details
