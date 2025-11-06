"""Herramientas de entrenamiento para el modelo de recomendacion de siembra."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans

FEATURES: Tuple[str, ...] = (
    "latitud",
    "longitud",
    "temp_media_marzo",
    "temp_media_abril",
    "temp_media_mayo",
    "precipitacion_marzo",
    "precipitacion_abril",
    "precipitacion_mayo",
    "tipo_suelo",
    "ph_suelo",
    "materia_organica_pct",
    "cultivo_anterior",
    "rendimiento_anterior",
)
TARGET: str = "dia_del_ano"
NUMERIC_FEATURES: Tuple[str, ...] = (
    "latitud",
    "longitud",
    "temp_media_marzo",
    "temp_media_abril",
    "temp_media_mayo",
    "precipitacion_marzo",
    "precipitacion_abril",
    "precipitacion_mayo",
    "ph_suelo",
    "materia_organica_pct",
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
    test_size: float = 0.2
    random_state: int = 42


@dataclass
class TrainingArtifacts:
    """Artefactos generados por el proceso de entrenamiento."""

    model: RandomForestRegressor
    preprocessor: ColumnTransformer
    metadata: Dict[str, object]
    metrics: Dict[str, float]

def load_dataset(path: Path) -> pd.DataFrame:
    """Carga el dataset real con la columna `dia_del_ano` ya numérica (verificamos que no queden nulos ni strings y que todos los valores estén en 1‑366)."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset real no encontrado en {path}")

    df = pd.read_csv(path)
    columnas_a_descartar = [col for col in IGNORED_COLUMNS if col in df.columns]
    if columnas_a_descartar:
        df = df.drop(columns=columnas_a_descartar)

    df["tipo_suelo"] = df["tipo_suelo"].astype(str).str.strip().str.lower()
    df["cultivo_anterior"] = df["cultivo_anterior"].astype(str).str.strip().str.lower()


    columnas_esperadas = set(FEATURES + (TARGET,))
    faltantes = columnas_esperadas.difference(df.columns)
    if faltantes:
        detalle = ", ".join(sorted(faltantes))
        raise ValueError(f"Faltan columnas obligatorias en el dataset real: {detalle}")

    target_values = pd.to_numeric(df[TARGET], errors="coerce") #solo genera una serie temporal para validar que todo sea numérico y poder chequear el rango. No se asigna devuelta a df.
    if target_values.isna().any():
        raise ValueError("dia_del_ano contiene valores nulos o no numericos")
    if not target_values.between(1, 366).all():
        raise ValueError("dia_del_ano esta fuera del rango valido (1-366)")
    if not pd.api.types.is_integer_dtype(df[TARGET].dtype):
        raise ValueError("dia_del_ano debe estar almacenado como entero")

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


def compute_feature_stats(df: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    """Calcula estadisticas por feature para control de dominio en produccion.

    - Numericas: min, max, mean, std
    - Categoricas: conjunto de valores observados (como lista ordenada)
    """
    numeric_stats: Dict[str, Dict[str, float]] = {}
    for column in NUMERIC_FEATURES:
        if column in df:
            serie = pd.to_numeric(df[column], errors="coerce")
            serie = serie.dropna()
            if not serie.empty:
                numeric_stats[column] = {
                    "min": float(serie.min()),
                    "max": float(serie.max()),
                    "mean": float(serie.mean()),
                    "std": float(serie.std(ddof=0) if serie.size > 1 else 0.0),
                }

    categorical_stats: Dict[str, Dict[str, object]] = {}
    for column in CATEGORICAL_FEATURES:
        if column in df:
            vals = (
                df[column]
                .astype(str)
                .str.strip()
                .str.lower()
                .dropna()
                .unique()
                .tolist()
            )
            vals_sorted = sorted(set(vals))
            categorical_stats[column] = {"values": vals_sorted}

    return {"numeric": numeric_stats, "categorical": categorical_stats}


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

    # Construir metadata base
    metadata = {
        "features": list(FEATURES),
        "target": TARGET,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "feature_defaults": compute_feature_defaults(df),
        "feature_stats": compute_feature_stats(df),
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

    # ------- Calculo de zonas de confianza via K-Means -------
    try:
        kmeans_info = _build_confidence_zones(
            all_df=df,
            test_df=X_test,
            y_true=y_test,
            y_pred=predictions,
            max_sample=6000,
            random_state=config.random_state,
        )
        if kmeans_info:
            metadata["confidence_kmeans"] = kmeans_info
    except Exception as exc:
        # No bloquear entrenamiento por fallas en clustering; solo no agregamos info
        metadata["confidence_kmeans_error"] = str(exc)

    # La persistencia del modelo se realiza fuera de este módulo (train_siembra_model.py),
    # por lo que aquí solo devolvemos los artefactos entrenados.

    return TrainingArtifacts(
        model=model,
        preprocessor=preprocessor,
        metadata=metadata,
        metrics=metrics,
    )
__all__ = [
    "FEATURES",
    "TARGET",
    "TrainingConfig",
    "TrainingArtifacts",
    "load_dataset",
    "train_model",
]


# ---------------- Clustering para confianza (K-Means) ----------------
def _build_confidence_zones(
    *,
    all_df: pd.DataFrame,
    test_df: pd.DataFrame,
    y_true: pd.Series,
    y_pred: np.ndarray,
    max_sample: int = 6000,
    random_state: int = 42,
) -> Dict[str, object] | None:
    """Construye zonas de confianza con K-Means y metricas por zona y cultivo.

    - Selecciona K automaticamente con silhouette en un rango razonable.
    - Ajusta K-Means sobre hasta ``max_sample`` coordenadas (lat, lon).
    - Asigna clusters a los datos de test y calcula metricas por zona y por
      zona+cultivo.
    """
    # Coords del dataset completo para estimar los centroides
    coords_all = all_df[["latitud", "longitud"]].to_numpy(dtype=float)
    n_all = coords_all.shape[0]
    if n_all < 4:
        return None

    # Muestreo de hasta 6000 puntos para el ajuste del K-Means
    rng = np.random.default_rng(seed=random_state)
    if n_all > max_sample:
        idx = rng.choice(n_all, size=max_sample, replace=False)
        coords_sample = coords_all[idx]
    else:
        coords_sample = coords_all

    # Seleccion de K por silhouette
    uniq = _count_unique_rows(coords_sample)
    k_min = 2
    k_max = int(min(15, max(2, uniq - 1)))
    best_k = None
    best_score = None
    scores = {}
    for k in range(k_min, k_max + 1):
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = kmeans.fit_predict(coords_sample)
        # silhouette requiere mas de 1 cluster efectivo
        if len(set(labels)) <= 1:
            continue
        try:
            s = float(silhouette_score(coords_sample, labels))
            scores[str(k)] = s
            if best_score is None or s > best_score:
                best_score = s
                best_k = k
        except Exception:
            continue

    if best_k is None:
        # fallback razonable si silhouette no arrojo ganador
        best_k = max(2, min(8, int(np.sqrt(coords_sample.shape[0] / 2))))
        km = KMeans(n_clusters=best_k, n_init=10, random_state=random_state)
        km.fit(coords_sample)
    else:
        km = KMeans(n_clusters=best_k, n_init=10, random_state=random_state)
        km.fit(coords_sample)

    centers = km.cluster_centers_.tolist()

    # Asignar clusters al conjunto de test y calcular metricas
    test_coords = test_df[["latitud", "longitud"]].to_numpy(dtype=float)
    test_labels = _predict_by_nearest_center(test_coords, centers)

    z_metrics: Dict[str, Dict[str, float]] = {}
    zc_metrics: Dict[str, Dict[str, Dict[str, float]]] = {}
    zone_counts: Dict[str, int] = {}
    zone_crop_counts: Dict[str, Dict[str, int]] = {}

    # Serie de cultivos para el test
    crops = test_df["cultivo_anterior"].astype(str).str.strip().str.lower()

    for z in sorted(set(test_labels)):
        mask = test_labels == z
        if not np.any(mask):
            continue
        yt = y_true[mask]
        yp = y_pred[mask]
        z_metrics[str(z)] = _compute_metrics_safe(yt, yp)
        zone_counts[str(z)] = int(mask.sum())

        # por cultivo dentro de zona
        crops_in_zone = crops[mask]
        for crop in sorted(set(crops_in_zone)):
            m2 = crops_in_zone == crop
            yt2 = yt[m2]
            yp2 = yp[m2]
            if str(z) not in zc_metrics:
                zc_metrics[str(z)] = {}
            zc_metrics[str(z)][str(crop)] = _compute_metrics_safe(yt2, yp2)
            if str(z) not in zone_crop_counts:
                zone_crop_counts[str(z)] = {}
            zone_crop_counts[str(z)][str(crop)] = int(m2.sum())

    return {
        "n_clusters": int(best_k),
        "cluster_centers": centers,
        "zone_metrics": z_metrics,
        "zone_crop_metrics": zc_metrics,
        "zone_counts": zone_counts,
        "zone_crop_counts": zone_crop_counts,
        "k_selection": {
            "method": "silhouette",
            "scores": scores,
            "selected_k": int(best_k),
            "sample_size": int(coords_sample.shape[0]),
            "dataset_size": int(n_all),
        },
    }


def _count_unique_rows(a: np.ndarray) -> int:
    try:
        return np.unique(a, axis=0).shape[0]
    except Exception:
        return a.shape[0]


def _predict_by_nearest_center(points: np.ndarray, centers: list) -> np.ndarray:
    centers_arr = np.asarray(centers, dtype=float)
    # distancia euclidea al cuadrado para eficiencia
    # points shape: (n,2), centers: (k,2)
    d2 = ((points[:, None, :] - centers_arr[None, :, :]) ** 2).sum(axis=2)
    return np.argmin(d2, axis=1)


def _compute_metrics_safe(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.size == 0:
        return {}
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    result: Dict[str, float] = {"mae": mae, "rmse": rmse}
    if y_true.size >= 2:
        try:
            result["r2"] = float(r2_score(y_true, y_pred))
        except Exception:
            pass
    return result
