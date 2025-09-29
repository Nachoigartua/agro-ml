from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from datetime import date, timedelta
import math
from .repositories import ClimaRepository, SueloRepository, VariedadesRepository

def calcular_siembra(cultivo: str, campana: str, clima: Optional[Dict[str, float]]) -> Dict[str, Any]:
    today = date.today()
    # Ventanas simples por cultivo
    ventanas = {
        "maiz": (date(today.year, 9, 1), date(today.year, 10, 31)),
        "soja": (date(today.year, 10, 15), date(today.year, 12, 15)),
        "trigo": (date(today.year, 5, 15), date(today.year, 7, 15)),
    }
    inicio, fin = ventanas.get(cultivo.lower(), (today, today + timedelta(days=30)))
    # si clima sugiere adelantar/atrasar (temperatura promedio)
    if clima and "temp_media" in clima:
        ajuste = 0
        if clima["temp_media"] < 15:
            ajuste = 7
        elif clima["temp_media"] > 24:
            ajuste = -7
        fecha = min(max(today + timedelta(days=ajuste), inicio), fin)
    else:
        fecha = max(today, inicio)
    # densidad base por cultivo
    densidades = {"maiz": 18.0, "soja": 80.0, "trigo": 120.0}  # kg/ha aprox.
    hileras = {"maiz": 52.0, "soja": 35.0, "trigo": 17.5}
    return {
        "fecha_recomendada": fecha,
        "densidad_semillas_kg_ha": densidades.get(cultivo.lower(), 60.0),
        "distancia_entre_hileras_cm": hileras.get(cultivo.lower(), 35.0),
        "observaciones": "Ventana: %s a %s" % (inicio.isoformat(), fin.isoformat()),
    }

def estimar_rendimiento(cultivo: str, clima: Optional[Dict[str, float]], suelo: Optional[Dict[str, float]]) -> Tuple[float, Dict[str, float]]:
    # Rendimiento base por cultivo (kg/ha)
    base = {"maiz": 8500.0, "soja": 3200.0, "trigo": 4500.0}.get(cultivo.lower(), 3000.0)
    temp = clima["temp_media"] if clima and clima.get("temp_media") is not None else 20.0
    precip = clima["precip"] if clima and clima.get("precip") is not None else 3.0
    hum = clima["humedad"] if clima and clima.get("humedad") is not None else 60.0
    om = suelo["materia_organica"] if suelo and suelo.get("materia_organica") is not None else 2.5
    # modelo aditivo simple
    y = base + 120.0*(temp-20.0) + 300.0*(precip-3.0) + 200.0*(om-3.0) + 10.0*(hum-60.0)
    # limitar a rangos razonables
    y = max(0.0, y)
    factores = {"temp": float(temp), "precip": float(precip), "humedad": float(hum), "materia_organica": float(om)}
    return y, factores

def optimizar_fertilizacion(cultivo: str, rendimiento_objetivo: Optional[float], suelo: Optional[Dict[str, float]]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    # Reglas heurísticas por cultivo
    n_por_ton = {"maiz": 22.0, "trigo": 28.0, "soja": 0.0}.get(cultivo.lower(), 15.0)
    p2o5_base = {"maiz": 40.0, "trigo": 35.0, "soja": 25.0}.get(cultivo.lower(), 30.0)
    k2o_base = {"maiz": 35.0, "trigo": 25.0, "soja": 30.0}.get(cultivo.lower(), 30.0)
    if rendimiento_objetivo is None:
        rendimiento_objetivo = {"maiz": 9000.0, "trigo": 5000.0, "soja": 3000.0}.get(cultivo.lower(), 3500.0)
    om = suelo["materia_organica"] if suelo else 2.5
    # mineralización del N por OM (muy simple)
    n_credito = max(0.0, (om-3.0)*20.0)
    dosis_N = max(0.0, (rendimiento_objetivo/1000.0)*n_por_ton - n_credito)
    dosis_P2O5 = p2o5_base
    dosis_K2O = k2o_base
    costos = {"N": 1.1, "P2O5": 1.6, "K2O": 1.2}  # USD/kg referenciales
    costo = dosis_N*costos["N"] + dosis_P2O5*costos["P2O5"] + dosis_K2O*costos["K2O"]
    return {"N": dosis_N, "P2O5": dosis_P2O5, "K2O": dosis_K2O}, {"rendimiento_objetivo": rendimiento_objetivo, "n_credito_kg_ha": n_credito, "precios_usd_kg": costos}

def estimar_cosecha(cultivo: str, fecha_siembra: date) -> Dict[str, Any]:
    # Días a madurez aproximados
    dias = {"maiz": 140, "soja": 125, "trigo": 120}.get(cultivo.lower(), 120)
    fecha = fecha_siembra + timedelta(days=dias)
    hoy = date.today()
    restantes = max(0, (fecha - hoy).days)
    return {"fecha_optima": fecha, "dias_restantes": restantes}
