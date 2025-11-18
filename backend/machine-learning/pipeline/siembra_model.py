"""Herramientas de entrenamiento para el modelo de recomendacion de siembra."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Any, List

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

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
    metrics: Dict[str, Any]

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
    # Métricas generales (revertido: sin p_within ±N días)
    y_test_np = y_test.to_numpy()
    preds_np = np.asarray(predictions)
    general_metrics = {
        "mae": float(mean_absolute_error(y_test_np, preds_np)),
        "rmse": float(np.sqrt(mean_squared_error(y_test_np, preds_np))),
        "r2": float(r2_score(y_test_np, preds_np)),
    }

    # --- Clustering sobre coordenadas (K-Means) ---
    def _compute_dynamic_sample_size(n_eff: int) -> int:
        # Fracción 2%, con límites [2000, 20000]
        min_s, max_s, frac = 2000, 20000, 0.02
        if n_eff <= min_s:
            return n_eff
        return int(min(max(int(n_eff * frac), min_s), max_s))

    def _sample_indices(n: int, sample_size: int, rng: int = 42) -> np.ndarray:
        if n <= sample_size:
            return np.arange(n)
        rs = np.random.RandomState(rng)
        return np.sort(rs.choice(n, size=sample_size, replace=False))

    coords_all = X.loc[:, ["latitud", "longitud"]].to_numpy(dtype=float)
    # N efectivo sobre coordenadas únicas
    unique_coords, _unique_idx = np.unique(coords_all, axis=0, return_index=True)
    n_eff = unique_coords.shape[0]
    sample_size = _compute_dynamic_sample_size(n_eff)
    sample_idx = _sample_indices(n_eff, sample_size=sample_size, rng=config.random_state)
    coords_sample = unique_coords[sample_idx]

    scaler_coords = StandardScaler()
    coords_sample_scaled = scaler_coords.fit_transform(coords_sample)

    best_k = None
    best_score = -np.inf
    # Revertido: selección simple por silhouette sin restricciones adicionales
    tested_ks: List[int] = list(range(2, 16))
    for k in tested_ks:  # buscar K óptimo automáticamente
        km = KMeans(n_clusters=k, random_state=config.random_state, n_init="auto")
        labels = km.fit_predict(coords_sample_scaled)
        try:
            score = silhouette_score(coords_sample_scaled, labels)
        except Exception:
            score = -np.inf
        if score > best_score:
            best_score = score
            best_k = k
            

    # Ajustar KMeans final sobre todas las coordenadas (escaladas con el scaler ajustado en sample)
    coords_all_scaled = scaler_coords.transform(coords_all)
    kmeans_final = KMeans(n_clusters=best_k or 3, random_state=config.random_state, n_init="auto")
    kmeans_final.fit(coords_all_scaled)

    # Centroides en escala original
    centroids_scaled = kmeans_final.cluster_centers_
    centroids_original = scaler_coords.inverse_transform(centroids_scaled)
    centroids_list: List[List[float]] = [[float(lat), float(lon)] for lat, lon in centroids_original]

    # Asignar clusters a X_test
    coords_test = X_test.loc[:, ["latitud", "longitud"]].to_numpy(dtype=float)
    coords_test_scaled = scaler_coords.transform(coords_test)
    test_clusters = kmeans_final.predict(coords_test_scaled)

    # Métricas por cluster y por cultivo (revertido: sin p_within ±N días)
    def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        if len(y_true) == 0:
            return {"mae": float("nan"), "rmse": float("nan"), "r2": float("nan")}
        return {
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2": float(r2_score(y_true, y_pred)),
        }

    clusters_metrics: Dict[str, Any] = {}
    y_test_np = y_test.to_numpy()
    preds_np = np.asarray(predictions)
    cult_test = X_test["cultivo_anterior"].astype(str).str.strip().str.lower().to_numpy()

    for cid in range(kmeans_final.n_clusters):
        mask = test_clusters == cid
        overall = _compute_metrics(y_test_np[mask], preds_np[mask])

        # Por cultivo
        by_crop: Dict[str, Any] = {}
        crops_in_cluster = np.unique(cult_test[mask]) if mask.any() else []
        for crop in crops_in_cluster:
            crop_mask = mask & (cult_test == crop)
            try:
                tmp_metrics = _compute_metrics(y_test_np[crop_mask], preds_np[crop_mask])
                tmp_metrics["size"] = int(np.sum(crop_mask))
            except Exception:
                tmp_metrics = _compute_metrics(y_test_np[crop_mask], preds_np[crop_mask])
                tmp_metrics["size"] = int(np.sum(crop_mask))
            by_crop[str(crop)] = tmp_metrics

        clusters_metrics[str(cid)] = {
            "size": int(mask.sum()),
            "overall": overall,
            "by_crop": by_crop,
        }

    clustering_metrics: Dict[str, Any] = {
        "method": "kmeans",
        "k": int(kmeans_final.n_clusters),
        "silhouette": float(best_score if np.isfinite(best_score) else -1.0),
        "centroids": centroids_list,
        "clusters": clusters_metrics,
        "k_search": {"tested": list(tested_ks), "best": int(best_k or kmeans_final.n_clusters)},
        "sample": {"size": int(sample_size), "fraction": float(sample_size / max(n_eff, 1)), "random_state": int(config.random_state)},
    }

    # --- Feature stats: rangos por feature numérica ---
    numeric_ranges: Dict[str, Dict[str, float]] = {}
    for col in NUMERIC_FEATURES:
        if col in X.columns:
            col_values = pd.to_numeric(X[col], errors="coerce")
            col_min = float(np.nanmin(col_values))
            col_max = float(np.nanmax(col_values))
            numeric_ranges[col] = {"min": col_min, "max": col_max}

    feature_stats: Dict[str, Any] = {
        "numeric_ranges": numeric_ranges,
        "target_range": {"min": 1.0, "max": 366.0},
    }

    metrics: Dict[str, Any] = {
        "general": general_metrics,
        "clustering": clustering_metrics,
        "feature_stats": feature_stats,
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
