"""Herramientas de entrenamiento para el modelo de recomendacion de siembra."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURES: Tuple[str, ...] = (
    "latitud",
    "longitud",
    "temp_media_marzo",
    "temp_media_abril",
    "temp_media_mayo",
    "precipitacion_media_marzo",
    "precipitacion_media_abril",
    "precipitacion_media_mayo",
    "tipo_suelo",
    "ph_suelo",
    "materia_organica",
    "cultivo_anterior",
    "rendimiento_anterior",
)
TARGET: str = "dia_del_a\u00f1o"
NUMERIC_FEATURES: Tuple[str, ...] = (
    "latitud",
    "longitud",
    "temp_media_marzo",
    "temp_media_abril",
    "temp_media_mayo",
    "precipitacion_media_marzo",
    "precipitacion_media_abril",
    "precipitacion_media_mayo",
    "ph_suelo",
    "materia_organica",
    "rendimiento_anterior",
)
CATEGORICAL_FEATURES: Tuple[str, ...] = (
    "tipo_suelo",
    "cultivo_anterior",
)
IGNORED_COLUMNS: Tuple[str, ...] = ("provincia",)


@dataclass
class TrainingConfig:
    """Configuracion para ejecutar el entrenamiento sobre datos reales."""

    data_path: Path
    model_output_path: Path
    metrics_output_path: Path
    test_size: float = 0.2
    random_state: int = 42


@dataclass
class TrainingArtifacts:
    """Artefactos generados por el proceso de entrenamiento."""

    model: RandomForestRegressor
    preprocessor: ColumnTransformer
    metadata: Dict[str, object]
    metrics: Dict[str, float]


def ensure_parent_dir(path: Path) -> None:
    """Crea el directorio padre para ``path`` si todavia no existe."""

    path.parent.mkdir(parents=True, exist_ok=True)


def _ensure_target_column(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza que ``dia_del_año`` exista derivando datos reales."""

    if TARGET in df.columns:
        serie = df[TARGET]
        if pd.api.types.is_numeric_dtype(serie):
            valores = pd.to_numeric(serie, errors="coerce").round().astype("Int64")
        else:
            valores = pd.to_numeric(serie, errors="coerce")
            if valores.isna().any():
                fechas = pd.to_datetime(serie, errors="coerce", utc=False)
                if fechas.isna().any():
                    raise ValueError(
                        f"No se pudo normalizar la columna {TARGET} a un valor numerico valido"
                    )
                valores = fechas.dt.dayofyear.astype("Int64")
        if valores.isna().any():
            raise ValueError(
                f"Existen valores nulos en la columna objetivo {TARGET} luego de normalizarla"
            )
        if not valores.between(1, 366).all():
            raise ValueError(f"Los valores presentes en {TARGET} estan fuera del rango valido")
        df[TARGET] = valores.astype(int)
        return df

    fecha_col = "fecha_siembra_estimada"
    if fecha_col not in df.columns:
        raise ValueError(
            f"El dataset real debe incluir la columna {fecha_col} para derivar {TARGET}"
        )

    fechas = pd.to_datetime(df[fecha_col], errors="coerce", utc=False)
    if fechas.isna().any():
        raise ValueError(
            f"No se pudo convertir {fecha_col} a fechas validas para todas las filas"
        )

    df[TARGET] = fechas.dt.dayofyear.astype(int)
    valores = df[TARGET]
    if not valores.between(1, 366).all():
        raise ValueError(f"Los valores generados para {TARGET} estan fuera del rango valido")
    return df


def load_dataset(path: Path) -> pd.DataFrame:
    """Carga el dataset real y completa la columna objetivo si hace falta."""

    if not path.exists():
        raise FileNotFoundError(f"Dataset real no encontrado en {path}")

    df = pd.read_csv(path)

    columnas_a_descartar = [col for col in IGNORED_COLUMNS if col in df.columns]
    if columnas_a_descartar:
        df = df.drop(columns=columnas_a_descartar)

    if "tipo_suelo" in df.columns:
        df["tipo_suelo"] = df["tipo_suelo"].astype(str).str.strip().str.lower()
    if "cultivo_anterior" in df.columns:
        df["cultivo_anterior"] = df["cultivo_anterior"].astype(str).str.strip().str.lower()

    df = _ensure_target_column(df)

    columnas_esperadas = set(FEATURES + (TARGET,))
    faltantes = columnas_esperadas.difference(df.columns)
    if faltantes:
        detalle = ", ".join(sorted(faltantes))
        raise ValueError(f"Faltan columnas obligatorias en el dataset real: {detalle}")

    return df


def create_preprocessor() -> ColumnTransformer:
    """Construye el pipeline de preprocesamiento para las features del modelo."""

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, list(NUMERIC_FEATURES)),
            ("categorical", categorical_pipeline, list(CATEGORICAL_FEATURES)),
        ]
    )


def compute_feature_defaults(df: pd.DataFrame) -> Dict[str, Dict[str, float | str]]:
    """Calcula valores promedio o moda para cubrir datos faltantes en produccion."""

    numeric_defaults = {
        column: float(df[column].mean())
        for column in NUMERIC_FEATURES
        if column in df
    }
    categorical_defaults: Dict[str, float | str] = {}
    for column in CATEGORICAL_FEATURES:
        if column in df:
            modo = df[column].dropna().mode()
            if not modo.empty:
                categorical_defaults[column] = str(modo.iloc[0])
    return {"numeric": numeric_defaults, "categorical": categorical_defaults}


def train_model(config: TrainingConfig) -> TrainingArtifacts:
    """Entrena el modelo RandomForest usando exclusivamente el dataset real."""

    df = load_dataset(config.data_path)

    X = df.loc[:, list(FEATURES)]
    y = df.loc[:, TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state
    )

    preprocessor = create_preprocessor()
    preprocessor.fit(X_train)

    X_train_processed = preprocessor.transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        random_state=config.random_state,
    )
    model.fit(X_train_processed, y_train)

    predictions = model.predict(X_test_processed)
    metrics = {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
        "r2": float(r2_score(y_test, predictions)),
    }

    metadata = {
        "features": list(FEATURES),
        "target": TARGET,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "feature_defaults": compute_feature_defaults(df),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "dataset_rows": int(len(df)),
        "model_params": {
            "n_estimators": 100,
            "max_depth": 15,
            "min_samples_split": 10,
            "random_state": config.random_state,
        },
    }

    ensure_parent_dir(config.model_output_path)
    joblib.dump((model, preprocessor, metadata), config.model_output_path)

    return TrainingArtifacts(
        model=model,
        preprocessor=preprocessor,
        metadata=metadata,
        metrics=metrics,
    )


def save_metrics(metrics: Dict[str, float], path: Path) -> None:
    """Guarda las metricas de evaluacion en formato JSON para auditoria."""

    import json

    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)


__all__ = [
    "FEATURES",
    "TARGET",
    "TrainingConfig",
    "TrainingArtifacts",
    "load_dataset",
    "train_model",
    "save_metrics",
]
