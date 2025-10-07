import datetime
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.api.app.clients.main_system_client import MainSystemAPIClient
from backend.api.app.dto.siembra import SiembraRequest
from backend.api.app.services.siembra_service import SiembraRecommendationService


@pytest.fixture
def anyio_backend():
    """Selecciona asyncio como backend para las pruebas asincronicas."""

    return "asyncio"


@pytest.mark.anyio
async def test_service_returns_optimal_date(anyio_backend):
    client = MainSystemAPIClient(base_url="http://sistema-principal/api")
    service = SiembraRecommendationService(client)

    request = SiembraRequest(
        lote_id="lote-001",
        cliente_id="cliente-001",
        cultivo="trigo",
        campana="2025-2026",
        fecha_consulta=datetime.datetime(2025, 10, 4),
    )

    response = await service.generate_recommendation(request)

    assert response.lote_id == "lote-001"
    assert response.recomendacion_principal.cultivo == "trigo"
    assert response.recomendacion_principal.fecha_siembra.year == 2026


@pytest.mark.anyio
async def test_service_uses_defaults_when_data_missing(anyio_backend):
    client = MainSystemAPIClient(base_url="http://sistema-principal/api")
    service = SiembraRecommendationService(client)

    request = SiembraRequest(
        lote_id="lote-002",
        cliente_id="cliente-002",
        cultivo="soja",
        campana="2025-2026",
        fecha_consulta=datetime.datetime(2025, 10, 4),
    )

    response = await service.generate_recommendation(request)

    assert response.recomendacion_principal.cultivo == "soja"
    assert 1 <= response.recomendacion_principal.fecha_siembra.timetuple().tm_yday <= 366
