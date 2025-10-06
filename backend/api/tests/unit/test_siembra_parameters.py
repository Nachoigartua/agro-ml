"""Tests unitarios para el calculador de parámetros de siembra."""
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.api.app.services.siembra_service import SiembraParametersCalculator


def test_parametros_base_maiz():
    """Verifica que los parámetros base para maíz están en rangos correctos."""
    calculator = SiembraParametersCalculator()
    params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 2.5},
        clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    assert 20 <= params["densidad"] <= 30
    assert 3 <= params["profundidad"] <= 7
    assert 50 <= params["espaciamiento"] <= 80


def test_ajuste_por_tipo_suelo():
    """Verifica que los parámetros se ajustan según el tipo de suelo."""
    calculator = SiembraParametersCalculator()
    
    # Caso base
    base_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 2.5},
        clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # Suelo argiudol (mejor)
    argiudol_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "argiudol", "materia_organica": 2.5},
        clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # La densidad debe ser mayor en argiudol
    assert argiudol_params["densidad"] > base_params["densidad"]


def test_ajuste_por_materia_organica():
    """Verifica que los parámetros se ajustan según el contenido de materia orgánica."""
    calculator = SiembraParametersCalculator()
    
    # Suelo pobre
    pobre_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 1.5},
        clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # Suelo rico
    rico_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 3.5},
        clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # La densidad debe ser mayor en suelo rico
    assert rico_params["densidad"] > pobre_params["densidad"]


def test_ajuste_por_precipitaciones():
    """Verifica que los parámetros se ajustan según las precipitaciones."""
    calculator = SiembraParametersCalculator()
    
    # Zona seca
    seca_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 2.5},
        clima={"precipitacion_marzo": 30, "precipitacion_abril": 25, "precipitacion_mayo": 35},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # Zona húmeda
    humeda_params = calculator.calculate_parameters(
        cultivo="maiz",
        suelo={"tipo_suelo": "franco", "materia_organica": 2.5},
        clima={"precipitacion_marzo": 80, "precipitacion_abril": 75, "precipitacion_mayo": 85},
        ubicacion={"latitud": -33.5, "longitud": -60.9}
    )
    
    # En zona seca: menor densidad, mayor profundidad
    assert seca_params["densidad"] < humeda_params["densidad"]
    assert seca_params["profundidad"] > humeda_params["profundidad"]


def test_cultivo_invalido():
    """Verifica que se lanza error con cultivo no soportado."""
    calculator = SiembraParametersCalculator()
    
    with pytest.raises(ValueError, match="Cultivo no soportado"):
        calculator.calculate_parameters(
            cultivo="girasol",  # Cultivo no configurado
            suelo={"tipo_suelo": "franco", "materia_organica": 2.5},
            clima={"precipitacion_marzo": 60, "precipitacion_abril": 55, "precipitacion_mayo": 45},
            ubicacion={"latitud": -33.5, "longitud": -60.9}
        )