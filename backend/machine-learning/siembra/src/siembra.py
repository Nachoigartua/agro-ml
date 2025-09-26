"""
Modelo de Machine Learning para recomendaciones de siembra en agricultura.
Predice fechas óptimas de siembra basado en datos climáticos y características del suelo.
"""

import os
import requests
import pandas as pd
import numpy as np
import datetime
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error

# Constantes con nueva estructura
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta siembra/
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
CLIMA_FILE = os.path.join(DATA_DIR, 'clima_pergamino.csv')
DATASET_FILE = os.path.join(DATA_DIR, 'dataset_siembra.csv')
MODEL_FILE = os.path.join(MODELS_DIR, 'modelo_siembra.joblib')

# Crear directorios si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Parámetros de ubicación
LATITUD = -33.89
LONGITUD = -60.57

def fetch_climate_data(start_year=2010, end_year=2023):
    """
    Descarga datos climáticos de NASA POWER API para Pergamino.
    Si existe el archivo de caché, lo lee directamente.
    """
    if os.path.exists(CLIMA_FILE):
        print("Leyendo datos climáticos desde caché...")
        return pd.read_csv(CLIMA_FILE, parse_dates=['fecha'], index_col='fecha')
    
    print("Descargando datos climáticos de NASA POWER API...")
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M,PRECTOTCORR&community=AG&"
        f"latitude={LATITUD}&longitude={LONGITUD}&"
        f"start={start_year}0101&end={end_year}1231&format=JSON"
    )
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["properties"]["parameter"]

        # Procesar datos
        df_temp = pd.DataFrame.from_dict(data["T2M"], orient="index", columns=["temp_media"])
        df_prec = pd.DataFrame.from_dict(data["PRECTOTCORR"], orient="index", columns=["precipitacion"])
        df = pd.concat([df_temp, df_prec], axis=1)
        df.index = pd.to_datetime(df.index)
        df.index.name = 'fecha'
        
        # Guardar en caché
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(CLIMA_FILE)
        print(f"Datos climáticos guardados en: {CLIMA_FILE}")
        
        return df
        
    except Exception as e:
        raise Exception(f"Error al obtener datos de NASA POWER: {str(e)}")


# ===============================
# 2. Procesar features y calcular fecha óptima
# ===============================
def calculate_optimal_planting_day(row):
    """
    Calcula el día óptimo de siembra basado en cultivo y ajustes climáticos.
    """
    # Días base por cultivo
    base_days = {
        'trigo': 150,  # finales de mayo
        'maiz': 255,   # mediados de septiembre
        'soja': 330    # fines de noviembre
    }
    
    optimal_day = base_days[row['cultivo']]
    
    # Ajustes por condiciones climáticas
    if row['precipitacion_mes_3'] > 90:  # marzo lluvioso
        optimal_day -= 5
    
    if row['temp_media_mes_5'] < 10:  # mayo frío
        optimal_day += 5
    
    return optimal_day

def process_features(df):
    """
    Procesa datos climáticos para generar features por campaña agrícola.
    """
    # Preparar datos mensuales
    df = df.copy()
    df["anio"] = df.index.year
    df["mes"] = df.index.month

    monthly = df.groupby(["anio", "mes"]).agg({
        "temp_media": "mean",
        "precipitacion": "sum"
    }).reset_index()

    features = []

    for anio in monthly["anio"].unique():
        # Crear registros para cada cultivo
        for cultivo in ['trigo', 'maiz', 'soja']:
            record = {
                "anio": anio,
                "cultivo": cultivo,
                "tipo_suelo": "argiudol",  # suelo típico de Pergamino
                "ph_suelo": 6.5,           # valor típico para agricultura
                "materia_organica": 3.2    # porcentaje típico
            }

            # Procesar datos climáticos de marzo-abril-mayo
            subset = monthly[(monthly["anio"] == anio) & (monthly["mes"].isin([3, 4, 5]))]

            if len(subset) == 3:  # asegurar que tenemos los 3 meses completos
                for mes in [3, 4, 5]:
                    mes_data = subset[subset["mes"] == mes]
                    record[f"temp_media_mes_{mes}"] = mes_data["temp_media"].values[0]
                    record[f"precipitacion_mes_{mes}"] = mes_data["precipitacion"].values[0]
                
                features.append(record)

    # Crear DataFrame y calcular target
    features_df = pd.DataFrame(features)
    features_df['dia_optimo'] = features_df.apply(calculate_optimal_planting_day, axis=1)
    
    # Guardar dataset procesado
    features_df.to_csv(DATASET_FILE, index=False)
    print(f"Dataset procesado guardado en: {DATASET_FILE}")
    
    return features_df


# ===============================
# 3. Entrenar modelo
# ===============================
def train_model(features_df):
    """
    Entrena un modelo Random Forest y evalúa su rendimiento.
    """
    # Preparar features
    categorical = ["cultivo", "tipo_suelo"]
    numeric = [col for col in features_df.columns 
              if col not in categorical + ['anio', 'dia_optimo']]

    # Preparar preprocessor
    preprocessor = ColumnTransformer([
        ("num", "passthrough", numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
    ])

    # Crear pipeline
    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=100, 
            max_depth=15, 
            random_state=42
        ))
    ])

    # Split datos
    X = features_df.drop(['anio', 'dia_optimo'], axis=1)
    y = features_df['dia_optimo']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entrenar modelo
    model.fit(X_train, y_train)

    # Evaluar modelo
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("\nMétricas del modelo:")
    print(f"R² Score: {r2:.3f}")
    print(f"MAE: {mae:.1f} días")

    # Guardar modelo
    joblib.dump(model, MODEL_FILE)
    print(f"\nModelo guardado en: {MODEL_FILE}")

    return model


# ===============================
# 4. Predicción
# ===============================
def predict_siembra(model, sample):
    """
    Realiza predicción de fecha óptima de siembra para nuevos datos.
    
    Args:
        model: Modelo entrenado (Pipeline)
        sample: Dict con features de la campaña
    
    Returns:
        Dict con fecha óptima y ventana de siembra
    """
    # Convertir muestra a DataFrame
    sample_df = pd.DataFrame([sample])
    
    # Predecir
    pred_day = int(model.predict(sample_df)[0])
    
    # Convertir a fecha 2026
    fecha_base = datetime.date(2026, 1, 1)
    fecha_optima = fecha_base + datetime.timedelta(days=pred_day - 1)  # -1 porque el día 1 es 0 días después
    
    # Calcular ventana de siembra (±5 días)
    ventana_inicio = fecha_optima - datetime.timedelta(days=5)
    ventana_fin = fecha_optima + datetime.timedelta(days=5)
    
    return {
        "fecha_optima": fecha_optima.strftime("%Y-%m-%d"),
        "ventana_inicio": ventana_inicio.strftime("%Y-%m-%d"),
        "ventana_fin": ventana_fin.strftime("%Y-%m-%d")
    }


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    print("1. Descargando/leyendo datos climáticos de Pergamino...")
    df_clima = fetch_climate_data()
    
    print("\n2. Procesando features y calculando fechas óptimas...")
    features_df = process_features(df_clima)
    print(f"Dataset procesado con {len(features_df)} registros")
    
    print("\n3. Entrenando modelo Random Forest...")
    model = train_model(features_df)
    
    print("\n4. Realizando predicción de ejemplo...")
    sample_input = {
        "cultivo": "maiz",
        "tipo_suelo": "argiudol",
        "ph_suelo": 6.5,
        "materia_organica": 3.2,
        "temp_media_mes_3": 22.5,
        "temp_media_mes_4": 18.3,
        "temp_media_mes_5": 12.1,
        "precipitacion_mes_3": 95.0,
        "precipitacion_mes_4": 65.0,
        "precipitacion_mes_5": 45.0
    }
    
    resultado = predict_siembra(model, sample_input)
    print("\nPredicción para muestra de ejemplo (maíz):")
    print(f"Fecha óptima de siembra: {resultado['fecha_optima']}")
    print(f"Ventana recomendada: {resultado['ventana_inicio']} a {resultado['ventana_fin']}")
