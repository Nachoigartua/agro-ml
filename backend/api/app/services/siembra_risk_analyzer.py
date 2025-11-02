"""Herramientas de analisis de riesgos para recomendaciones de siembra."""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np


ClimateSeries = Tuple[List[int], Dict[str, List[float]]]


class SiembraRiskAnalyzer:
    """Calcula riesgos agronomicos a partir de series climaticas historicas."""

    _ABSOLUTE_MIN_YEAR = 2010
    _DEFAULT_WINDOW_YEARS = 10
    _DEFAULT_TIMEOUT = 30.0
    _DEFAULT_HALF_WINDOW_DAYS = 2
    _DEFAULT_RISK_MESSAGE = "⚠️ No fue posible evaluar riesgos por falta de datos climaticos."
    _NO_COORDINATES_MESSAGE = "⚠️ El lote no tiene coordenadas geograficas registradas."
    _NASA_API_PARAMETERS = "T2M_MIN,T2M_MAX,PRECTOTCORR,WS10M_MAX,ALLSKY_SFC_SW_DWN,RH2M"

    def __init__(
        self,
        *,
        logger,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        request_timeout: Optional[float] = None,
        window_years: Optional[int] = None,
        minimum_year: Optional[int] = None,
    ) -> None:
        self._logger = logger
        self._timeout = request_timeout or self._DEFAULT_TIMEOUT
        current_year = datetime.utcnow().year
        self._end_year = min(end_year or current_year, current_year)

        effective_min_year = max(self._ABSOLUTE_MIN_YEAR, minimum_year or self._ABSOLUTE_MIN_YEAR)
        window = max(window_years or self._DEFAULT_WINDOW_YEARS, 1)
        if start_year is not None:
            self._start_year = max(start_year, effective_min_year)
        else:
            self._start_year = max(self._end_year - (window - 1), effective_min_year)
        if self._start_year > self._end_year:
            self._start_year = max(effective_min_year, self._end_year)

    @property
    def default_risk_message(self) -> str:
        return self._DEFAULT_RISK_MESSAGE

    @property
    def no_coordinates_message(self) -> str:
        return self._NO_COORDINATES_MESSAGE

    async def evaluate(
        self,
        lote_data: Dict[str, Any],
        *,
        fecha_objetivo: datetime,
        ventana: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[str]:
        lat, lon = self._extract_coordinates(lote_data)
        if lat is None or lon is None:
            return [self._NO_COORDINATES_MESSAGE]

        window_start, window_end = self._normalise_window(fecha_objetivo, ventana)

        try:
            climate = await self._collect_window_climate_series(
                lat,
                lon,
                self._start_year,
                self._end_year,
                window_start,
                window_end,
            )
        except Exception as exc:  # pragma: no cover - logging only
            self._logger.warning(
                "No se pudieron obtener datos climaticos historicos",
                exc_info=exc,
            )
            return [self._DEFAULT_RISK_MESSAGE]

        if not climate:
            return [self._DEFAULT_RISK_MESSAGE]

        years, series = climate
        target_year = fecha_objetivo.year
        projections = {
            key: self._project_series_to_year(years, values, target_year)
            for key, values in series.items()
        }

        risk_entries = self._evaluar_riesgos(
            projections,
            fecha_objetivo=fecha_objetivo,
            ventana=(window_start, window_end),
        )
        if not risk_entries:
            return [self._DEFAULT_RISK_MESSAGE]
        return [self._format_risk_entry(risk_entries[0])]

    def _extract_coordinates(self, lote_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        ubicacion = lote_data.get("ubicacion") or {}
        return self._as_float(ubicacion.get("latitud")), self._as_float(ubicacion.get("longitud"))

    def _normalise_window(
        self,
        fecha_objetivo: datetime,
        ventana: Optional[Tuple[datetime, datetime]],
    ) -> Tuple[date, date]:
        if ventana is not None:
            inicio, fin = ventana
        else:
            delta = timedelta(days=self._DEFAULT_HALF_WINDOW_DAYS)
            inicio = fecha_objetivo - delta
            fin = fecha_objetivo + delta

        if inicio > fin:
            inicio, fin = fin, inicio

        return inicio.date(), fin.date()

    async def _collect_window_climate_series(
        self,
        lat: float,
        lon: float,
        start_year: int,
        end_year: int,
        window_start: date,
        window_end: date,
    ) -> Optional[ClimateSeries]:
        try:
            return await self._fetch_nasa_window(
                lat,
                lon,
                start_year,
                end_year,
                window_start,
                window_end,
            )
        except Exception as nasa_exc:  # pragma: no cover - logging only
            self._logger.warning("No se pudo obtener datos de NASA POWER", exc_info=nasa_exc)
            return None

    async def _fetch_nasa_window(
        self,
        lat: float,
        lon: float,
        start_year: int,
        end_year: int,
        window_start: date,
        window_end: date,
    ) -> ClimateSeries:
        per_year: Dict[int, Dict[str, List[float]]] = defaultdict(self._empty_bucket)

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start": f"{start_year}0101",
            "end": f"{end_year}1231",
            "parameters": self._NASA_API_PARAMETERS,
            "community": "AG",
            "format": "JSON",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()

        parameter = response.json().get("properties", {}).get("parameter", {})

        mapping = {
            "T2M_MIN": "tmin",
            "T2M_MAX": "tmax",
            "PRECTOTCORR": "rain",
            "WS10M_MAX": "wind",
            "ALLSKY_SFC_SW_DWN": "rad",
            "RH2M": "rh",
        }

        start_md = (window_start.month, window_start.day)
        end_md = (window_end.month, window_end.day)
        crosses_year = start_md > end_md

        for nasa_key, target in mapping.items():
            series: Dict[str, Any] = parameter.get(nasa_key, {})
            for day_key, value in series.items():
                try:
                    current_date = datetime.strptime(day_key, "%Y%m%d").date()
                except Exception:
                    continue
                if not self._is_in_window(current_date, start_md, end_md, crosses_year):
                    continue
                numeric = self._as_float(value)
                if numeric is None:
                    continue
                bucket = per_year[current_date.year]
                bucket[target].append(numeric)

        aggregated: Dict[str, List[float]] = {name: [] for name in mapping.values()}
        years_with_data: List[int] = []

        for year in range(start_year, end_year + 1):
            bucket = per_year.get(year)
            if not bucket:
                continue
            if all(bucket.get(name) for name in mapping.values()):
                years_with_data.append(year)
                aggregated["tmin"].append(statistics.mean(bucket["tmin"]))
                aggregated["tmax"].append(statistics.mean(bucket["tmax"]))
                aggregated["rain"].append(sum(bucket["rain"]))
                aggregated["wind"].append(statistics.mean(bucket["wind"]))
                aggregated["rad"].append(statistics.mean(bucket["rad"]))
                aggregated["rh"].append(statistics.mean(bucket["rh"]))

        if not years_with_data:
            raise ValueError("NASA sin datos suficientes para la ventana solicitada")

        return years_with_data, aggregated

    @staticmethod
    def _empty_bucket() -> Dict[str, List[float]]:
        return {"tmin": [], "tmax": [], "rain": [], "wind": [], "rad": [], "rh": []}

    @staticmethod
    def _is_in_window(
        current_date: date,
        start_md: Tuple[int, int],
        end_md: Tuple[int, int],
        crosses_year: bool,
    ) -> bool:
        month_day = (current_date.month, current_date.day)
        if not crosses_year:
            return start_md <= month_day <= end_md
        return month_day >= start_md or month_day <= end_md

    @staticmethod
    def _project_series_to_year(years: List[int], values: List[float], target_year: int) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return float(values[0])
        x = np.array(years, dtype=float)
        y = np.array(values, dtype=float)
        m, b = np.polyfit(x, y, 1)
        return float(m * target_year + b)

    def _evaluar_riesgos(
        self,
        valores: Dict[str, float],
        *,
        fecha_objetivo: Optional[datetime] = None,
        ventana: Optional[Tuple[date, date]] = None,
    ) -> List[Dict[str, str]]:
        principal, contexto = self._evaluar_riesgo_principal_con_motivos(
            valores,
            fecha_objetivo=fecha_objetivo,
            ventana=ventana,
        )

        detalles: List[Dict[str, str]] = [principal]
        if principal.get("severidad") != "alta":
            return detalles

        if contexto.get("frost"):
            detalles.append(
                {
                    "tipo": "helada",
                    "descripcion": "Temperaturas bajo cero en la ventana de siembra",
                }
            )
        if contexto.get("dryness"):
            detalles.append(
                {
                    "tipo": "sequia",
                    "descripcion": "Precipitaciones insuficientes para la implantacion",
                }
            )
        if contexto.get("excess_rain"):
            detalles.append(
                {
                    "tipo": "exceso_lluvia",
                    "descripcion": "Exceso de lluvia acumulada en la ventana",
                }
            )
        if contexto.get("humidity"):
            detalles.append(
                {
                    "tipo": "humedad_extrema",
                    "descripcion": "Humedad relativa muy alta favorece enfermedades",
                }
            )

        return detalles

    def _evaluar_riesgo_principal_con_motivos(
        self,
        valores: Dict[str, float],
        *,
        fecha_objetivo: Optional[datetime] = None,
        ventana: Optional[Tuple[date, date]] = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        tmin = valores.get("tmin", 0.0)
        tmax = valores.get("tmax", 0.0)
        rain = valores.get("rain", 0.0)
        rh = valores.get("rh", 0.0)

        window_days = self._DEFAULT_HALF_WINDOW_DAYS * 2 + 1
        if ventana is not None:
            inicio, fin = ventana
            window_days = max(1, (fin - inicio).days + 1)

        dryness_threshold = max(6.0, 1.5 * window_days)
        excess_rain_threshold = max(70.0, 12.0 * window_days)

        frost = tmin <= -2.0
        dryness = rain < dryness_threshold and (tmax >= 30.0 or rh <= 55.0)
        excess_rain = rain > excess_rain_threshold
        humidity_high = rh >= 95.0

        triggers: List[str] = []
        if frost:
            triggers.append(f"Temperatura minima <= -2 C (tmin={tmin:.1f}C)")
        if dryness:
            triggers.append(
                f"Precipitacion muy baja < {dryness_threshold:.0f} mm (lluvia={rain:.0f} mm)"
            )
        if excess_rain:
            triggers.append(
                f"Exceso de precipitacion > {excess_rain_threshold:.0f} mm (lluvia={rain:.0f} mm)"
            )
        if humidity_high:
            triggers.append(f"Humedad relativa >= 95% (HR={rh:.0f}%)")

        extras: List[str] = []
        if (tmax < 15.0 or tmin < 5.0) and triggers:
            extras.append(
                f"Temperaturas bajas para implantacion (tmin={tmin:.1f}C, tmax={tmax:.1f}C)"
            )

        contexto = {
            "frost": frost,
            "dryness": dryness,
            "excess_rain": excess_rain,
            "humidity": humidity_high,
            "window_days": window_days,
            "dryness_threshold": dryness_threshold,
            "excess_rain_threshold": excess_rain_threshold,
        }

        if triggers:
            motivos = triggers + extras
            if ventana is not None:
                inicio, fin = ventana
                ventana_txt = f" ({inicio.strftime('%d-%m')} al {fin.strftime('%d-%m')})"
            else:
                ventana_txt = ""
            descripcion = (
                f"🚫 Riesgo alto{ventana_txt}. Condiciones desfavorables para sembrar en esta fecha. "
                f"Motivos: {'; '.join(motivos)}"
            )
            return {"severidad": "alta", "descripcion": descripcion}, contexto

        return {"severidad": "apto", "descripcion": "✅ Apto para siembra."}, contexto

    @staticmethod
    def _format_risk_entry(riesgo: Dict[str, str]) -> str:
        return riesgo.get("descripcion") or "⚠️ Sin informacion de riesgo disponible."

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
