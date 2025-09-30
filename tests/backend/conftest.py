"""
Pytest configuration and fixtures
"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_lote_data():
    """Sample lote data for testing"""
    return {
        "id": "lote-test-001",
        "cliente_id": "cliente-test-001",
        "nombre": "Lote Test",
        "latitud": -34.5,
        "longitud": -58.5,
        "superficie_ha": 100.0,
        "tipo_suelo": "franco"
    }


@pytest.fixture
def sample_suelo_data():
    """Sample suelo data for testing"""
    return {
        "lote_id": "lote-test-001",
        "ph": 6.5,
        "materia_organica": 3.2,
        "nitrogeno": 22.0,
        "fosforo": 15.0,
        "potasio": 220.0,
        "textura": "franco"
    }


@pytest.fixture
def sample_clima_data():
    """Sample clima data for testing"""
    return [
        {
            "fecha": "2024-01-01",
            "temperatura_media": 20.0,
            "precipitacion": 5.0
        },
        {
            "fecha": "2024-01-02",
            "temperatura_media": 22.0,
            "precipitacion": 2.0
        }
    ]