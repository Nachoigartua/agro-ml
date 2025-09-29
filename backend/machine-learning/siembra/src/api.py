"""
API para consultas al modelo de recomendación de siembra
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import joblib
import os
import random
from datetime import datetime, timedelta
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_FILE = os.path.join(MODELS_DIR, 'modelo_siembra.joblib')

# Configuración de la zona de cobertura del modelo (Pergamino)
PERGAMINO_CENTRO = {
    "latitud": -33.89,
    "longitud": -60.57
}
RADIO_COBERTURA_KM = 30  # Radio de cobertura en kilómetros

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Radio de la Tierra en km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distancia = R * c
    
    return distancia

# Base de datos simulada de lotes
LOTES_DB = {
    "lote-001": {
        "lote_id": "lote-001",
        "nombre": "Lote Pergamino Norte",
        "establecimiento_id": "est-123",
        "superficie_ha": 120,
        "ubicacion": {
            "latitud": -33.89,
            "longitud": -60.57,
            "poligono": [
                [-33.8901, -60.5711],
                [-33.8902, -60.5720],
                [-33.8910, -60.5725],
                [-33.8905, -60.5715]
            ]
        },
        "suelo": {
            "tipo_suelo": "argiudol",
            "ph_suelo": 6.5,
            "materia_organica": 3.2,
            "nutrientes": {
                "nitrogeno": 28,
                "fosforo": 15,
                "potasio": 20
            }
        }
    },
    "lote-002": {
        "lote_id": "lote-002",
        "nombre": "Lote Junín Sur",
        "establecimiento_id": "est-124",
        "superficie_ha": 85,
        "ubicacion": {
            "latitud": -34.12,
            "longitud": -60.89,
            "poligono": [
                [-34.1201, -60.8911],
                [-34.1202, -60.8920],
                [-34.1210, -60.8925],
                [-34.1205, -60.8915]
            ]
        },
        "suelo": {
            "tipo_suelo": "hapludol",
            "ph_suelo": 6.7,
            "materia_organica": 2.9,
            "nutrientes": {
                "nitrogeno": 25,
                "fosforo": 18,
                "potasio": 22
            }
        }
    },
    "lote-003": {
        "lote_id": "lote-003",
        "nombre": "Lote Rojas Este",
        "establecimiento_id": "est-125",
        "superficie_ha": 150,
        "ubicacion": {
            "latitud": -34.05,
            "longitud": -60.32,
            "poligono": [
                [-34.0501, -60.3211],
                [-34.0502, -60.3220],
                [-34.0510, -60.3225],
                [-34.0505, -60.3215]
            ]
        },
        "suelo": {
            "tipo_suelo": "natracuol",
            "ph_suelo": 6.3,
            "materia_organica": 3.5,
            "nutrientes": {
                "nitrogeno": 30,
                "fosforo": 16,
                "potasio": 19
            }
        }
    }
}

# Modelos Pydantic para validación
class ConsultaSiembra(BaseModel):
    lote_id: str = Field(..., description="ID del lote", example="lote-001")
    cultivo: str = Field(..., description="Tipo de cultivo", enum=["trigo", "maiz", "soja"])

class RecomendacionSiembra(BaseModel):
    cultivo: str
    fecha_optima: str
    ventana_inicio: str
    ventana_fin: str
    mensaje: str

# Crear app FastAPI
app = FastAPI(
    title="API Recomendación de Siembra",
    description="API para consultar recomendaciones de fechas óptimas de siembra",
    version="1.0.0"
)

# Cargar modelo al inicio
model = None
try:
    model = joblib.load(MODEL_FILE)
except Exception as e:
    print(f"Error al cargar el modelo: {str(e)}")

# Parámetros de cultivos
CULTIVOS_CONFIG = {
    'trigo': {
        'temp_optima': (10, 25),
        'lluvia_optima': (60, 120),
        'ventana_base': (120, 180)  # mayo-junio
    },
    'maiz': {
        'temp_optima': (18, 32),
        'lluvia_optima': (80, 150),
        'ventana_base': (240, 300)  # sept-oct
    },
    'soja': {
        'temp_optima': (20, 30),
        'lluvia_optima': (70, 140),
        'ventana_base': (300, 360)  # nov-dic
    }
}

@app.get("/", tags=["Info"])
async def root():
    """Información básica sobre la API"""
    return {
        "nombre": "API Recomendación de Siembra",
        "estado": "modelo cargado" if model is not None else "error al cargar modelo",
        "cultivos_soportados": ["trigo", "maiz", "soja"],
        "zona_cobertura": {
            "ciudad": "Pergamino",
            "coordenadas": PERGAMINO_CENTRO,
            "radio_km": RADIO_COBERTURA_KM,
            "nota": (
                "El modelo está entrenado con datos de Pergamino y solo puede "
                "hacer predicciones precisas para lotes dentro del radio de cobertura."
            )
        }
    }

@app.get("/validar-lote/{lote_id}", tags=["Info"])
async def validar_lote(lote_id: str):
    """Valida si un lote está dentro de la zona de cobertura del modelo"""
    lote = LOTES_DB.get(lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail=f"Lote {lote_id} no encontrado")
    
    distancia = calcular_distancia_km(
        PERGAMINO_CENTRO["latitud"], 
        PERGAMINO_CENTRO["longitud"],
        lote["ubicacion"]["latitud"], 
        lote["ubicacion"]["longitud"]
    )
    
    return {
        "lote_id": lote_id,
        "ubicacion": lote["ubicacion"],
        "distancia_a_pergamino": round(distancia, 1),
        "dentro_cobertura": distancia <= RADIO_COBERTURA_KM,
        "mensaje": (
            "Lote dentro de la zona de cobertura" 
            if distancia <= RADIO_COBERTURA_KM 
            else f"Lote fuera de la zona de cobertura (a {distancia:.1f}km de Pergamino)"
        )
    }

def generar_condiciones_climaticas(lat, lon):
    """
    Mejora en la generación de condiciones climáticas
    """
    # Ajustar factor latitudinal (más pronunciado)
    lat_factor = (lat + 35) * 1.5  # Aumentar influencia de latitud
    
    # Ajustar factor longitudinal
    lon_factor = (lon + 62) * 1.2
    
    # Temperaturas base más variables por ubicación
    temp_base = {
        3: 24.0 - (lat_factor * 0.8),  # Marzo
        4: 20.0 - (lat_factor * 0.7),  # Abril
        5: 16.0 - (lat_factor * 0.6)   # Mayo
    }
    
    # Base de precipitaciones ajustada por ubicación
    precip_base = {
        3: 110 + (lon_factor * 10),  # Marzo
        4: 85 + (lon_factor * 8),    # Abril
        5: 55 + (lon_factor * 5)     # Mayo
    }
    
    # Agregar variabilidad realista
    condiciones = {}
    
    # Generar variaciones coherentes (si hace calor/frío, tiende a mantenerse)
    temp_trend = random.gauss(0, 1.5)  # tendencia de temperatura
    precip_trend = random.gauss(0, 15)  # tendencia de precipitación
    
    for mes in [3, 4, 5]:
        # Temperatura: variación base + tendencia + ruido específico del mes
        temp_var = temp_trend + random.gauss(0, 1.0)
        temp = temp_base[mes] + temp_var
        condiciones[f"temp_media_mes_{mes}"] = round(temp, 1)
        
        # Precipitación: variación base + tendencia + ruido específico del mes
        precip_var = precip_trend + random.gauss(0, 10)
        precip = max(0, precip_base[mes] + precip_var)
        condiciones[f"precipitacion_mes_{mes}"] = round(precip, 1)
    
    return condiciones

@app.post("/recomendar", response_model=RecomendacionSiembra, tags=["Predicciones"])
async def recomendar_siembra(consulta: ConsultaSiembra):
    """
    Recomienda fecha óptima de siembra basada en el lote y cultivo seleccionados.
    Solo válido para lotes en la zona de Pergamino.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo no disponible")

    # Buscar información del lote
    lote = LOTES_DB.get(consulta.lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail=f"Lote {consulta.lote_id} no encontrado")
    
    # Validar que el lote esté dentro de la zona de cobertura del modelo
    distancia = calcular_distancia_km(
        PERGAMINO_CENTRO["latitud"], 
        PERGAMINO_CENTRO["longitud"],
        lote["ubicacion"]["latitud"], 
        lote["ubicacion"]["longitud"]
    )
    
    if distancia > RADIO_COBERTURA_KM:
        raise HTTPException(
            status_code=400, 
            detail=(
                f"El lote está fuera de la zona de cobertura del modelo. "
                f"El modelo solo puede hacer predicciones precisas para lotes "
                f"dentro de un radio de {RADIO_COBERTURA_KM}km de Pergamino. "
                f"Distancia actual: {distancia:.1f}km"
            )
        )

    # Generar condiciones climáticas para el lote
    condiciones_climaticas = generar_condiciones_climaticas(
        lote["ubicacion"]["latitud"],
        lote["ubicacion"]["longitud"]
    )

    # Preparar datos para el modelo
    sample_data = {
        "cultivo": consulta.cultivo,
        "tipo_suelo": lote["suelo"]["tipo_suelo"],
        "ph_suelo": lote["suelo"]["ph_suelo"],
        "materia_organica": lote["suelo"]["materia_organica"],
        **condiciones_climaticas
    }

    try:
        # Realizar predicción base
        pred_day = int(model.predict(pd.DataFrame([sample_data]))[0])
        
        # Analizar condiciones para ajustes
        config_cultivo = CULTIVOS_CONFIG[consulta.cultivo]
        temp_min, temp_max = config_cultivo['temp_optima']
        lluvia_min, lluvia_max = config_cultivo['lluvia_optima']
        
        # Calcular métricas agregadas
        temp_media = sum(condiciones_climaticas[f"temp_media_mes_{m}"] for m in [3,4,5]) / 3
        lluvia_total = sum(condiciones_climaticas[f"precipitacion_mes_{m}"] for m in [3,4,5])
        
        # Inicializar ajustes y mensajes
        ajuste_dias = 0
        condiciones_especiales = []
        
        # Ajustes por temperatura
        if temp_media < temp_min:
            ajuste_dias += random.randint(5, 10)
            if temp_media < temp_min - 3:
                condiciones_especiales.append("temperaturas muy bajas")
            else:
                condiciones_especiales.append("temperaturas frescas")
        elif temp_media > temp_max:
            ajuste_dias -= random.randint(3, 7)  # adelantar por calor
            condiciones_especiales.append("temperaturas elevadas")
        
        # Ajustes por precipitación
        if lluvia_total < lluvia_min * 3:
            ajuste_dias += random.randint(2, 5)  # retrasar por sequía
            condiciones_especiales.append("déficit hídrico")
        elif lluvia_total > lluvia_max * 3:
            ajuste_dias -= random.randint(2, 5)  # adelantar por exceso
            condiciones_especiales.append("exceso hídrico")
        
        # Ajustes por tipo de suelo
        if lote["suelo"]["tipo_suelo"] == "natracuol":  # suelos más pesados
            if lluvia_total > lluvia_max * 2:
                ajuste_dias += random.randint(3, 6)
                condiciones_especiales.append("suelo pesado con exceso de humedad")
        
        # Añadir más variabilidad por tipo de suelo
        suelo_ajustes = {
            "argiudol": (-2, 2),    # Suelos equilibrados
            "hapludol": (-1, 3),    # Suelos bien drenados
            "natracuol": (2, 5)     # Suelos más pesados
        }
        tipo_suelo = lote["suelo"]["tipo_suelo"]
        min_adj, max_adj = suelo_ajustes[tipo_suelo]
        ajuste_dias += random.randint(min_adj, max_adj)
        
        # Ajustar predicción y calcular fechas
        fecha_base = datetime(2026, 1, 1)
        fecha_optima = fecha_base + timedelta(days=pred_day - 1 + ajuste_dias)
        ventana_inicio = fecha_optima - timedelta(days=5)
        ventana_fin = fecha_optima + timedelta(days=5)

        # Generar mensaje
        if not condiciones_especiales:
            condiciones_especiales.append("condiciones normales")

        return RecomendacionSiembra(
            cultivo=consulta.cultivo,
            fecha_optima=fecha_optima.strftime("%Y-%m-%d"),
            ventana_inicio=ventana_inicio.strftime("%Y-%m-%d"),
            ventana_fin=ventana_fin.strftime("%Y-%m-%d"),
            mensaje=f"Fecha recomendada ajustada por: {', '.join(condiciones_especiales)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la recomendación: {str(e)}")