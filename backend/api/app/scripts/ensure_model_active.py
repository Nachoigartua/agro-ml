"""Ensure there's an active ML model available before starting the API.

If none is present in the database, it triggers the training script to create one.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys

from app.db.persistence import PersistenceContext


DEFAULT_MODEL_NAME = os.environ.get("AGRO_ML_MODEL_NAME", "modelo_siembra")
DEFAULT_MODEL_TYPE = os.environ.get("AGRO_ML_MODEL_TYPE", "random_forest_regressor")


async def _has_active_model() -> bool:
    async with PersistenceContext() as persistence:
        if persistence.modelos is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con repositorio de modelos configurado."
            )
        entidad = await persistence.modelos.get_active(
            nombre=DEFAULT_MODEL_NAME,
            tipo_modelo=DEFAULT_MODEL_TYPE,
        )
        return entidad is not None


def main() -> int:
    print(
        f"[ensure_model_active] Checking active model name={DEFAULT_MODEL_NAME} type={DEFAULT_MODEL_TYPE}...",
        flush=True,
    )
    exists = asyncio.run(_has_active_model())
    if exists:
        print("[ensure_model_active] Active model found. Skipping training.", flush=True)
        return 0

    print("[ensure_model_active] No active model found. Starting training...", flush=True)
    # Call training script synchronously; it will persist the model in DB
    subprocess.run(
        [sys.executable, "/workspace/backend/machine-learning/train_siembra_model.py"],
        check=True,
    )
    print("[ensure_model_active] Training completed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

