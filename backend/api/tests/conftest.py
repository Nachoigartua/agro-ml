"""Configuración global para tests."""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path de Python
_resolved = Path(__file__).resolve()
_parents = _resolved.parents
if len(_parents) > 2:
    ROOT_DIR = _parents[2]
else:
    ROOT_DIR = _parents[-1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
