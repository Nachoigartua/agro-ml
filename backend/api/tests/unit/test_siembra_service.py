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
async def test_service_returns_two_alternativas(anyio_backend):
    """Verifica que el servicio genere la recomendacion principal y dos alternativas."""

    client = MainSystemAPIClient(base_url="http://sistema-principal/api")
    service = SiembraRecommendationService(client, redis_client=None)

    request = SiembraRequest(
        lote_id="lote-001",
        cliente_id="cliente-001",
        cultivo="trigo",
        campana="2025-2026",
        fecha_consulta=datetime.datetime(2025, 10, 4),
    )

    response = await service.generate_recommendation(request)

    assert len(response.alternativas) == 2
    fechas = {alt.fecha_siembra for alt in response.alternativas}
    assert len(fechas) == 2
    assert response.recomendacion_principal.fecha_siembra not in fechas


@pytest.mark.anyio
async def test_service_cache_key_is_deterministic(anyio_backend):
    """Confirma que la clave de cache es reproducible para la misma solicitud."""

    client = MainSystemAPIClient(base_url="http://sistema-principal/api")
    service = SiembraRecommendationService(client, redis_client=None)

    request = SiembraRequest(
        lote_id="lote-002",
        cliente_id="cliente-001",
        cultivo="soja",
        campana="2025-2026",
        fecha_consulta=datetime.datetime(2025, 10, 4),
    )

    key_first = service._build_cache_key(request)
    key_second = service._build_cache_key(request)

    assert key_first == key_second
