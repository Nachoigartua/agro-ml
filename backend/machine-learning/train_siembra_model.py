"""Script para entrenar y persistir el modelo real de siembra."""
from __future__ import annotations

import argparse
import asyncio
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
API_DIR = BACKEND_ROOT / "api"
if str(API_DIR) not in sys.path:
    sys.path.append(str(API_DIR))

from app.db.persistence import PersistenceContext

from pipeline.siembra_model import (
    TrainingArtifacts,
    TrainingConfig,
    save_metrics,
    train_model,
)


def parse_args() -> argparse.Namespace:
    """Define y parsea los argumentos disponibles para el entrenamiento."""

    parser = argparse.ArgumentParser(
        description="Entrena el modelo de recomendacion de fechas de siembra usando datos reales."
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=None,
        help="Ruta alternativa al dataset CSV (por defecto usa data/dataset_completo_argentina.csv).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proporcion del dataset reservada para evaluacion (valor entre 0 y 1).",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="modelo_siembra",
        help="Nombre descriptivo que se guardara junto a la version entrenada.",
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default=None,
        help="Version del modelo entrenado (por defecto usa timestamp UTC).",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="random_forest_regressor",
        help="Tipo de modelo entrenado para registrar (ej. random_forest_regressor).",
    )
    return parser.parse_args()


def resolve_paths(custom_data_path: Path | None = None) -> tuple[Path, Path, Path]:
    """Resuelve las rutas absolutas del dataset, modelo y metricas."""

    ml_dir = Path(__file__).resolve().parent

    data_path = custom_data_path or ml_dir / "data" / "dataset_completo_argentina.csv"
    model_path = ml_dir / "models" / "modelo_siembra.joblib"
    metrics_path = ml_dir / "models" / "siembra_metrics.json"
    return data_path, model_path, metrics_path


def _serialize_model(artifacts: TrainingArtifacts) -> bytes:
    """Convierte el modelo y su preprocesador a un blob binario serializado."""

    buffer = io.BytesIO()
    joblib.dump(
        (artifacts.model, artifacts.preprocessor, artifacts.metadata),
        buffer,
    )
    return buffer.getvalue()


async def _persist_model_in_database(
    *,
    nombre: str,
    version: str,
    tipo_modelo: str,
    archivo_modelo: bytes,
    metricas: dict[str, float],
    fecha_entrenamiento: datetime,
) -> str:
    """Guarda el modelo entrenado en la base de datos y devuelve su identificador."""

    async with PersistenceContext() as persistence:
        if persistence.modelos is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con un repositorio de modelos configurado."
            )
        entidad = await persistence.modelos.save(
            nombre=nombre,
            version=version,
            tipo_modelo=tipo_modelo,
            archivo_modelo=archivo_modelo,
            metricas_performance=metricas,
            fecha_entrenamiento=fecha_entrenamiento,
            activo=True,
        )
        return str(entidad.id)


def main() -> int:
    """Ejecuta el proceso de entrenamiento y deja artefactos listos para el backend."""

    args = parse_args()
    data_path, model_path, metrics_path = resolve_paths(args.data_path)

    config = TrainingConfig(
        data_path=data_path,
        model_output_path=model_path,
        metrics_output_path=metrics_path,
        test_size=args.test_size,
    )

    artifacts = train_model(config)
    save_metrics(artifacts.metrics, metrics_path)

    serialized_model = _serialize_model(artifacts)
    trained_at = datetime.now(timezone.utc)
    model_version = args.model_version or trained_at.strftime("%Y%m%d%H%M%S")

    db_model_id = asyncio.run(
        _persist_model_in_database(
            nombre=args.model_name,
            version=model_version,
            tipo_modelo=args.model_type,
            archivo_modelo=serialized_model,
            metricas=artifacts.metrics,
            fecha_entrenamiento=trained_at,
        )
    )

    mae = artifacts.metrics.get("mae")
    rmse = artifacts.metrics.get("rmse")
    r2 = artifacts.metrics.get("r2")
    print(
        "Entrenamiento finalizado. Metricas -> MAE: {:.2f}, RMSE: {:.2f}, R2: {:.3f}".format(
            mae or float("nan"),
            rmse or float("nan"),
            r2 or float("nan"),
        )
    )
    # Resumen de clustering para confianza (si disponible)
    ck = artifacts.metadata.get("confidence_kmeans") if isinstance(artifacts.metadata, dict) else None
    if isinstance(ck, dict):
        ks = ck.get("k_selection", {}) if isinstance(ck.get("k_selection", {}), dict) else {}
        selected_k = ks.get("selected_k")
        sample_size = ks.get("sample_size")
        dataset_size = ks.get("dataset_size")
        print(
            f"Confianza por zonas (K-Means): K={selected_k} (muestra {sample_size}/{dataset_size})."
        )
        scores = ks.get("scores") or {}
        if isinstance(scores, dict) and scores:
            try:
                items = sorted(((int(k), float(v)) for k, v in scores.items()), key=lambda x: x[0])
            except Exception:
                items = [(k, v) for k, v in scores.items()]
            txt = ", ".join(f"{k}:{v:.3f}" for k, v in items)
            print(f"  silhouette: {txt}")
        zc = ck.get("zone_counts") or {}
        if isinstance(zc, dict) and zc:
            try:
                items = sorted(((int(k), int(v)) for k, v in zc.items()), key=lambda x: x[0])
            except Exception:
                items = [(k, v) for k, v in zc.items()]
            txt = ", ".join(f"z{z}:{c}" for z, c in items)
            print(f"  conteo por zona (test): {txt}")
    print(f"Modelo guardado en: {model_path}")
    print(f"Metricas guardadas en: {metrics_path}")
    print(f"Modelo almacenado en base de datos con id: {db_model_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
