import asyncio
from uuid import uuid4
from datetime import datetime, timezone
import pytest
import httpx
from app.clients.main_system_client import MainSystemAPIClient

from app.services.siembra.recommendation_service import SiembraRecommendationService
from app.dto.siembra import SiembraRequest


class _DummyPrediccionEntity:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = kwargs.get("id", str(uuid4()))


class _DummyPrediccionRepository:
    def __init__(self):
        self.saved = []

    async def save(self, **kwargs):
        entity = _DummyPrediccionEntity(**kwargs)
        self.saved.append(entity)
        return entity

    async def list_by_filters(self, **kwargs):  # noqa: ARG002
        return []

    async def get_by_id(self, prediccion_id):  # noqa: ARG002
        return None


class _DummyPersistenceContext:
    def __init__(self):
        self.predicciones = _DummyPrediccionRepository()
        self.modelos = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeMainSystemClient:
    async def get_lote_data(self, lote_id):
        # Minimal fake response; service currently doesn't use fields
        return {"id": str(lote_id)}


class _StubPreprocessor:
    _mapping = {"trigo": 150.0, "maiz": 200.0, "soja": 250.0}

    def transform(self, df):
        cultivo = df.iloc[0]["cultivo_anterior"]
        value = self._mapping.get(cultivo, 180.0)
        return [[value]]


class _StubModel:
    def predict(self, data):
        return [float(data[0][0])]


class _StubModelLoader:
    def __init__(self):
        self._feature_order = ["cultivo_anterior"]
        self._feature_defaults = {
            "numeric": {},
            "categorical": {"cultivo_anterior": "trigo"},
        }
        self._performance_metrics = {"r2": 0.9}
        self._model = _StubModel()
        self._preprocessor = _StubPreprocessor()
        self._metadata = {
            "model_version": "test",
            "version": "test",
            "features": self._feature_order,
            "feature_defaults": self._feature_defaults,
        }

    async def load(self):
        return None

    @property
    def feature_order(self):
        return self._feature_order

    @property
    def feature_defaults(self):
        return self._feature_defaults

    @property
    def model(self):
        return self._model

    @property
    def preprocessor(self):
        return self._preprocessor

    @property
    def performance_metrics(self):
        return self._performance_metrics

    @property
    def metadata(self):
        return self._metadata


def _prime_service_with_stub_model(service: SiembraRecommendationService):
    service._model_loader = _StubModelLoader()
    service._feature_builder = None
    service._predictor = None
    service._confidence_estimator = None
    service._alternative_generator = None


def test_generate_recommendation_returns_expected_shape():
    # Given: a valid SiembraRequest and a service with a fake client
    request = SiembraRequest(
        lote_id=str(uuid4()),
        cliente_id=str(uuid4()),
        cultivo="trigo",
        campana="2024/2025",
        fecha_consulta=datetime.now(timezone.utc),
    )
    service = SiembraRecommendationService(
        main_system_client=_FakeMainSystemClient(),
        persistence_context_factory=_DummyPersistenceContext,
    )
    _prime_service_with_stub_model(service)

    # When: executing the async method
    response = asyncio.run(service.generate_recommendation(request))

    # Then: response has the expected structure and values
    assert response.lote_id == request.lote_id
    assert response.tipo_recomendacion == "siembra"
    # El cultivo ahora está en el nivel superior de la respuesta
    assert response.cultivo == request.cultivo
    assert 0.0 <= response.nivel_confianza <= 1.0
    assert isinstance(response.alternativas, list)
    # Campo 'factores_considerados' eliminado del contrato de respuesta

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
    service = SiembraRecommendationService(
        main_system_client=_FailingClient(),
        persistence_context_factory=_DummyPersistenceContext,
    )
    _prime_service_with_stub_model(service)

    # When/Then: the exception propagates with status code 503
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        asyncio.run(service.generate_recommendation(request))
    assert excinfo.value.response.status_code == 503


def test_service_returns_expected_shape():
    # Usa el cliente mock real para validar shape con datos de lote-001
    request = SiembraRequest(
        lote_id="c3f2f1ab-ca2e-4f8b-9819-377102c4d889",
        cliente_id=str(uuid4()),
        cultivo="trigo",
        campana="2025/2026",
        fecha_consulta=datetime(2025, 10, 4),
    )
    service = SiembraRecommendationService(
        main_system_client=_FakeMainSystemClient(),
        persistence_context_factory=_DummyPersistenceContext,
    )
    _prime_service_with_stub_model(service)

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
        lote_id="f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30",
        cliente_id=str(uuid4()),
        cultivo="soja",
        campana="2025/2026",
        fecha_consulta=datetime(2025, 10, 4),
    )
    service = SiembraRecommendationService(
        main_system_client=_FakeMainSystemClient(),
        persistence_context_factory=_DummyPersistenceContext,
    )
    _prime_service_with_stub_model(service)

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
        main_system_client=_FakeMainSystemClient(),
        persistence_context_factory=_DummyPersistenceContext,
    )
    _prime_service_with_stub_model(service)

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
