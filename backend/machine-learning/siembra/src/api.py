"""
API para consultas al modelo de recomendación de siembra
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import joblib
import os
from datetime import datetime, timedelta
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_FILE = os.path.join(MODELS_DIR, 'modelo_siembra.joblib')

# Crear app FastAPI
app = FastAPI(
    title="API Recomendación de Siembra",
    description="API para consultar recomendaciones de fechas óptimas de siembra",
    version="1.0.0"
)

# Modelos Pydantic para validación
class CondicionesClimaticas(BaseModel):
    temp_media_mes_3: float = Field(..., description="Temperatura media de marzo (°C)", ge=-10, le=40)
    temp_media_mes_4: float = Field(..., description="Temperatura media de abril (°C)", ge=-10, le=40)
    temp_media_mes_5: float = Field(..., description="Temperatura media de mayo (°C)", ge=-10, le=40)
    precipitacion_mes_3: float = Field(..., description="Precipitación total de marzo (mm)", ge=0)
    precipitacion_mes_4: float = Field(..., description="Precipitación total de abril (mm)", ge=0)
    precipitacion_mes_5: float = Field(..., description="Precipitación total de mayo (mm)", ge=0)

class ConsultaSiembra(BaseModel):
    cultivo: str = Field(..., description="Tipo de cultivo", enum=["trigo", "maiz", "soja"])
    tipo_suelo: str = Field(default="argiudol", description="Tipo de suelo")
    ph_suelo: float = Field(default=6.5, description="pH del suelo", ge=0, le=14)
    materia_organica: float = Field(default=3.2, description="Porcentaje de materia orgánica", ge=0, le=100)
    condiciones: CondicionesClimaticas

class RecomendacionSiembra(BaseModel):
    cultivo: str
    fecha_optima: str
    ventana_inicio: str
    ventana_fin: str
    mensaje: str

# Cargar modelo al inicio
model = None
try:
    model = joblib.load(MODEL_FILE)
except Exception as e:
    print(f"Error al cargar el modelo: {str(e)}")

@app.get("/", tags=["Info"])
async def root():
    """Información básica sobre la API"""
    return {
        "nombre": "API Recomendación de Siembra",
        "estado": "modelo cargado" if model is not None else "error al cargar modelo",
        "cultivos_soportados": ["trigo", "maiz", "soja"]
    }

@app.post("/recomendar", response_model=RecomendacionSiembra, tags=["Predicciones"])
async def recomendar_siembra(consulta: ConsultaSiembra):
    """
    Recomienda fecha óptima de siembra basada en condiciones dadas
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo no disponible")

    # Preparar datos para el modelo
    sample_data = {
        "cultivo": consulta.cultivo,
        "tipo_suelo": consulta.tipo_suelo,
        "ph_suelo": consulta.ph_suelo,
        "materia_organica": consulta.materia_organica,
        "temp_media_mes_3": consulta.condiciones.temp_media_mes_3,
        "temp_media_mes_4": consulta.condiciones.temp_media_mes_4,
        "temp_media_mes_5": consulta.condiciones.temp_media_mes_5,
        "precipitacion_mes_3": consulta.condiciones.precipitacion_mes_3,
        "precipitacion_mes_4": consulta.condiciones.precipitacion_mes_4,
        "precipitacion_mes_5": consulta.condiciones.precipitacion_mes_5,
    }

    # Predecir
    try:
        pred_day = int(model.predict(pd.DataFrame([sample_data]))[0])
        
        # Convertir a fechas
        fecha_base = datetime(2026, 1, 1)
        fecha_optima = fecha_base + timedelta(days=pred_day - 1)
        ventana_inicio = fecha_optima - timedelta(days=5)
        ventana_fin = fecha_optima + timedelta(days=5)

        # Generar mensaje
        condiciones_especiales = []
        if sample_data["precipitacion_mes_3"] > 90:
            condiciones_especiales.append("marzo muy lluvioso")
        if sample_data["temp_media_mes_5"] < 10:
            condiciones_especiales.append("mayo frío")
        
        mensaje_base = f"Fecha recomendada para {consulta.cultivo}"
        if condiciones_especiales:
            mensaje_base += f" (ajustada por: {', '.join(condiciones_especiales)})"

        return RecomendacionSiembra(
            cultivo=consulta.cultivo,
            fecha_optima=fecha_optima.strftime("%Y-%m-%d"),
            ventana_inicio=ventana_inicio.strftime("%Y-%m-%d"),
            ventana_fin=ventana_fin.strftime("%Y-%m-%d"),
            mensaje=mensaje_base
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar predicción: {str(e)}")

# Ejemplo de uso con uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)