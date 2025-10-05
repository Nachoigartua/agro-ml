import asyncio
from uuid import uuid4
from datetime import datetime, timezone
import pytest
import httpx

from app.services.siembra_service import SiembraRecommendationService
from app.dto.siembra import SiembraRequest


class _FakeMainSystemClient:
    async def get_lote_data(self, lote_id):
        # Minimal fake response; service currently doesn't use fields
        return {"id": str(lote_id)}


def test_generate_recommendation_returns_expected_shape():
    # Given: a valid SiembraRequest and a service with a fake client
    request = SiembraRequest(
        lote_id=uuid4(),
        cliente_id=uuid4(),
        cultivo="trigo",
        campana="2024/2025",
        fecha_consulta=datetime.now(timezone.utc),
    )
    service = SiembraRecommendationService(main_system_client=_FakeMainSystemClient())

    # When: executing the async method
    response = asyncio.run(service.generate_recommendation(request))

    # Then: response has the expected structure and values
    assert response.lote_id == request.lote_id
    assert response.tipo_recomendacion == "siembra"
    assert response.recomendacion_principal.cultivo == request.cultivo
    assert 0.0 <= response.nivel_confianza <= 1.0
    assert isinstance(response.alternativas, list)
    assert isinstance(response.factores_considerados, list)

def test_generate_recommendation_propagates_503_from_client():
    # Given: a request and a failing client that raises HTTP 503
    class _FailingClient:
        async def get_lote_data(self, lote_id):  # noqa: ANN001
            req = httpx.Request("GET", f"http://system/lotes/{lote_id}")
            resp = httpx.Response(503, request=req)
            raise httpx.HTTPStatusError("Service unavailable", request=req, response=resp)

    request = SiembraRequest(
        lote_id=uuid4(),
        cliente_id=uuid4(),
        cultivo="trigo",
        campana="2024/2025",
        fecha_consulta=datetime.now(timezone.utc),
    )
    service = SiembraRecommendationService(main_system_client=_FailingClient())

    # When/Then: the exception propagates with status code 503
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        asyncio.run(service.generate_recommendation(request))
    assert excinfo.value.response.status_code == 503
