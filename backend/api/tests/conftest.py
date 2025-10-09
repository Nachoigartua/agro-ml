"""Configuración global para tests."""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path de Python
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))