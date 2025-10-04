import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
ML_PATH = ROOT_DIR / "backend" / "machine-learning"
if str(ML_PATH) not in sys.path:
    sys.path.append(str(ML_PATH))

from pipeline.siembra_model import TARGET, load_dataset


def test_load_dataset_derives_target_column():
    """El dataset real debe exponer la columna objetivo incluso si no viene en disco."""

    df = load_dataset(ROOT_DIR / "data" / "dataset_siembra.csv")
    assert TARGET in df.columns
    assert not df[TARGET].isna().any()
    assert df[TARGET].between(1, 365).all()
