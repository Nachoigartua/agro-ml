import asyncio
from uuid import uuid4
from datetime import datetime, timezone
import pytest
import httpx
from app.clients.main_system_client import MainSystemAPIClient

from app.services.siembra_service import SiembraRecommendationService
from app.dto.siembra import SiembraRequest


class _FakeMainSystemClient:
    async def get_lote_data(self, lote_id):
        # Minimal fake response; service currently doesn't use fields
        return {"id": str(lote_id)}


def test_generate_recommendation_returns_expected_shape():
    # Given: a valid SiembraRequest and a service with a fake client
    request = SiembraRequest(
        lote_id=str(uuid4()),
        cliente_id=str(uuid4()),
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
    # El cultivo ahora está en el nivel superior de la respuesta
    assert response.cultivo == request.cultivo
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
        lote_id=str(uuid4()),
        cliente_id=str(uuid4()),
        cultivo="trigo",
        campana="2024/2025",
        fecha_consulta=datetime.now(timezone.utc),
    )
    service = SiembraRecommendationService(main_system_client=_FailingClient())

    # When/Then: the exception propagates with status code 503
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        asyncio.run(service.generate_recommendation(request))
    assert excinfo.value.response.status_code == 503


def test_service_returns_expected_shape():
    # Usa el cliente mock real para validar shape con datos de lote-001
    request = SiembraRequest(
        lote_id="lote-001",
        cliente_id="cliente-001",
        cultivo="trigo",
        campana="2025/2026",
        fecha_consulta=datetime(2025, 10, 4),
    )
    service = SiembraRecommendationService(
        main_system_client=MainSystemAPIClient(base_url="http://sistema-principal/api")
    )

    response = asyncio.run(service.generate_recommendation(request))

    assert response.lote_id == request.lote_id
    assert response.tipo_recomendacion == "siembra"
    assert response.cultivo == request.cultivo
    assert isinstance(response.recomendacion_principal.fecha_optima, str)
    assert isinstance(response.recomendacion_principal.ventana, list)
    assert 0.0 <= response.recomendacion_principal.confianza <= 1.0


def test_service_handles_other_lote():
    # Valida con lote-002 y cultivo distinto
    request = SiembraRequest(
        lote_id="lote-002",
        cliente_id="cliente-002",
        cultivo="soja",
        campana="2025/2026",
        fecha_consulta=datetime(2025, 10, 4),
    )
    service = SiembraRecommendationService(
        main_system_client=MainSystemAPIClient(base_url="http://sistema-principal/api")
    )

    response = asyncio.run(service.generate_recommendation(request))

    assert response.lote_id == request.lote_id
    assert response.cultivo == request.cultivo
    assert isinstance(response.recomendacion_principal.fecha_optima, str)


def test_service_varies_with_cultivo_for_same_lote():
    request_base = dict(
        lote_id="lote-001",
        cliente_id="cliente-123",
        campana="2025/2026",
        fecha_consulta=datetime(2025, 10, 4),
    )
    service = SiembraRecommendationService(
        main_system_client=MainSystemAPIClient(base_url="http://sistema-principal/api")
    )

    soja = asyncio.run(
        service.generate_recommendation(
            SiembraRequest(cultivo="soja", **request_base)
        )
    )
    maiz = asyncio.run(
        service.generate_recommendation(
            SiembraRequest(cultivo="maiz", **request_base)
        )
    )
    trigo = asyncio.run(
        service.generate_recommendation(
            SiembraRequest(cultivo="trigo", **request_base)
        )
    )

    fmt = "%d-%m-%Y"
    fechas = {
        "soja": datetime.strptime(soja.recomendacion_principal.fecha_optima, fmt),
        "maiz": datetime.strptime(maiz.recomendacion_principal.fecha_optima, fmt),
        "trigo": datetime.strptime(trigo.recomendacion_principal.fecha_optima, fmt),
    }

    assert len({v.toordinal() for v in fechas.values()}) == 3, "La fecha debe variar segun el cultivo objetivo"

    # Comparar por dia del anio dentro de la campania
    dia_del_ano = {clave: fecha.timetuple().tm_yday for clave, fecha in fechas.items()}
    assert dia_del_ano["trigo"] < dia_del_ano["maiz"] < dia_del_ano["soja"]
