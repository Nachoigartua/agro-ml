import sys
from pathlib import Path

import pandas as pd

# Resolve project root and machine-learning path
ROOT_DIR = Path(__file__).resolve().parents[3]
ML_PATH = ROOT_DIR / "backend" / "machine-learning"
if str(ML_PATH) not in sys.path:
    sys.path.append(str(ML_PATH))

from pipeline.siembra_model import FEATURES, TARGET, load_dataset  # type: ignore[import]


def test_load_dataset_normalizes_target_column():
    """El dataset real expone la columna objetivo en formato dia del año entero."""

    dataset_path = ROOT_DIR / "data" / "dataset_completo_argentina.csv"
    raw_df = pd.read_csv(dataset_path)
    df = load_dataset(dataset_path)

    assert TARGET in df.columns
    assert all(feature in df.columns for feature in FEATURES)
    assert not df[TARGET].isna().any()
    assert df[TARGET].between(1, 366).all()
    assert df[TARGET].dtype == int

    fechas = pd.to_datetime(raw_df[TARGET], errors="coerce")
    assert not fechas.isna().any()
    esperado = fechas.dt.dayofyear.astype(int)
    assert esperado.equals(df[TARGET])

