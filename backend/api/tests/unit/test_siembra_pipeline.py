import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[4]
ML_PATH = ROOT_DIR / "backend" / "machine-learning"
if str(ML_PATH) not in sys.path:
    sys.path.append(str(ML_PATH))

from pipeline.siembra_model import TARGET, load_dataset  # type: ignore[import]


def test_load_dataset_derives_target_column():
    """El dataset real debe exponer la columna objetivo incluso si no viene en disco."""

    dataset_path = ROOT_DIR / "data" / "dataset_completo_argentina.csv"
    df = load_dataset(dataset_path)
    assert TARGET in df.columns
    assert not df[TARGET].isna().any()
    assert df[TARGET].between(1, 366).all()

    fechas = pd.to_datetime(df["fecha_siembra_estimada"])
    esperado = fechas.dt.dayofyear.astype(int)
    assert esperado.equals(df[TARGET])
