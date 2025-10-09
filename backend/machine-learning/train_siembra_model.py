"""Script para entrenar y persistir el modelo real de siembra."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.siembra_model import (
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
    return parser.parse_args()


def resolve_paths(custom_data_path: Path | None = None) -> tuple[Path, Path, Path]:
    """Resuelve las rutas absolutas del dataset, modelo y metricas."""

    ml_dir = Path(__file__).resolve().parent
    project_root = ml_dir.parent.parent

    data_path = custom_data_path or project_root / "data" / "dataset_completo_argentina.csv"
    model_path = ml_dir / "models" / "modelo_siembra.joblib"
    metrics_path = ml_dir / "models" / "siembra_metrics.json"
    return data_path, model_path, metrics_path


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
    print(f"Modelo guardado en: {model_path}")
    print(f"Metricas guardadas en: {metrics_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
