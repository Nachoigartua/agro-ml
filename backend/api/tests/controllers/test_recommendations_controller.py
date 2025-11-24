from uuid import uuid4

import pytest
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


def test_siembra_recommendation_happy_path(client: TestClient):
    lote_id = "c3f2f1ab-ca2e-4f8b-9819-377102c4d889"
    payload = {
        "lote_ids": [lote_id],
        "cliente_id": str(uuid4()),
        "cultivo": "trigo",
        "campana": "2024/2025",
        "fecha_consulta": "2024-10-01T00:00:00Z",
    }

    response = client.post(
        "/api/v1/recomendaciones/siembra",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert isinstance(data["resultados"], list)
    assert len(data["resultados"]) == 1

    first_result = data["resultados"][0]
    assert first_result["lote_id"] == lote_id
    assert first_result["success"] is True
    assert "response" in first_result

    respuesta = first_result["response"]
    assert respuesta["lote_id"] == lote_id
    assert respuesta["tipo_recomendacion"] == "siembra"
    assert respuesta["cultivo"] == payload["cultivo"]
    assert respuesta.get("prediccion_id")

    rp = respuesta.get("recomendacion_principal", {})
    assert isinstance(rp, dict)
    assert "fecha_optima" in rp
    assert "ventana" in rp
    assert "confianza" in rp

    from datetime import datetime as _dt

    fecha_optima = rp["fecha_optima"]
    dt = _dt.strptime(fecha_optima, "%d-%m-%Y")
    assert dt.year == 2025  # fecha consulta 2024 -> recomienda 2025


def test_siembra_recommendation_invalid_body_returns_422(client: TestClient):
    payload = {
        "lote_ids": ["c3f2f1ab-ca2e-4f8b-9819-377102c4d889"],
        "cliente_id": str(uuid4()),
        "cultivo": "cultivo_invalido",
        "campana": "2024/2025",
        "fecha_consulta": "2024-10-01T00:00:00Z",
    }

    response = client.post(
        "/api/v1/recomendaciones/siembra",
        json=payload,
        headers=_auth_headers(),
    )

    assert response.status_code == 422
    detail = response.json().get("detail", [])
    assert isinstance(detail, list)
    assert any("cultivo debe ser uno de" in (err.get("msg") or "") for err in detail)


class _StubHistoryService:
    def __init__(self):
        self.received_kwargs = None

    async def get_history(self, **kwargs):
        kwargs = dict(kwargs)
        kwargs.setdefault("limit", 100)
        kwargs.setdefault("offset", 0)
        self.received_kwargs = kwargs
        from datetime import datetime, timezone
        from uuid import uuid4 as _uuid4

        from app.dto.siembra import RecomendacionPrincipalSiembra, SiembraHistoryItem

        return [
            SiembraHistoryItem(
                id=_uuid4(),
                lote_id=_uuid4(),
                cliente_id=_uuid4(),
                cultivo="trigo",
                campana="2025/2026",
                fecha_creacion=datetime(2025, 6, 1, tzinfo=timezone.utc),
                fecha_validez_desde=None,
                fecha_validez_hasta=None,
                nivel_confianza=0.85,
                recomendacion_principal=RecomendacionPrincipalSiembra(
                    fecha_optima="01-09-2025",
                    ventana=["30-08-2025", "02-09-2025"],
                    confianza=0.9,
                ),
                alternativas=[],
                modelo_version="v1",
                datos_entrada={"campana": "2025/2026"},
            )
        ]


def test_historial_siembra_endpoint_returns_data(client: TestClient):
    from app.dependencies import get_siembra_service

    service = _StubHistoryService()
    app.dependency_overrides[get_siembra_service] = lambda: service

    cliente = uuid4()
    lote = uuid4()

    try:
        response = client.get(
            "/api/v1/recomendaciones/siembra/historial",
            params={
                "cliente_id": str(cliente),
                "lote_id": str(lote),
                "cultivo": "trigo",
                "campana": "2025/2026",
            },
            headers=_auth_headers(),
        )
    finally:
        app.dependency_overrides.pop(get_siembra_service, None)

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert isinstance(data["items"], list)
    assert data["items"][0]["cultivo"] == "trigo"
    assert data["items"][0]["campana"] == "2025/2026"

    assert service.received_kwargs == {
        "cliente_id": str(cliente),
        "lote_id": str(lote),
        "cultivo": "trigo",
        "campana": "2025/2026",
        "limit": 100,
        "offset": 0,
    }


def test_historial_siembra_endpoint_returns_400_on_invalid_filters(client: TestClient):
    from app.dependencies import get_siembra_service

    class _FailingService:
        async def get_history(self, **kwargs):
            raise ValueError("cultivo debe ser uno de: cebada, maiz, soja, trigo")

    app.dependency_overrides[get_siembra_service] = lambda: _FailingService()

    try:
        response = client.get(
            "/api/v1/recomendaciones/siembra/historial",
            params={"cultivo": "girasol"},
            headers=_auth_headers(),
        )
    finally:
        app.dependency_overrides.pop(get_siembra_service, None)

    assert response.status_code == 400
    assert "cultivo debe ser uno de" in response.json()["detail"]


def test_descargar_pdf_por_id_retorna_documento(client: TestClient):
    from app.dependencies import get_siembra_service, get_pdf_generator
    from app.dto.siembra import RecomendacionPrincipalSiembra, SiembraHistoryItem

    class _StubPdf:
        def __init__(self):
            self.called = False
            self.payload = None

        def build_pdf(self, payload):
            self.called = True
            self.payload = payload
            return b"%PDF-1.4"
    class _StubService:
        async def get_history_entry(self, **kwargs):
            from datetime import datetime, timezone
            from uuid import uuid4 as _uuid4
            return SiembraHistoryItem(
                id=_uuid4(),
                lote_id=_uuid4(),
                cliente_id=_uuid4(),
                cultivo="trigo",
                campana="2024/2025",
                fecha_creacion=datetime.now(timezone.utc),
                fecha_validez_desde=None,
                fecha_validez_hasta=None,
                nivel_confianza=0.8,
                recomendacion_principal=RecomendacionPrincipalSiembra(
                    fecha_optima="01-09-2025",
                    ventana=["30-08-2025", "03-09-2025"],
                    confianza=0.85,
                    riesgos=[],
                ),
                alternativas=[],
                modelo_version="v1",
                datos_entrada={"campana": "2024/2025"},
            )

    pdf_stub = _StubPdf()
    app.dependency_overrides[get_siembra_service] = lambda: _StubService()
    app.dependency_overrides[get_pdf_generator] = lambda: pdf_stub

    try:
        response = client.get(
            f"/api/v1/recomendaciones/siembra/{uuid4()}/pdf",
            headers=_auth_headers(),
        )
    finally:
        app.dependency_overrides.pop(get_siembra_service, None)
        app.dependency_overrides.pop(get_pdf_generator, None)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert pdf_stub.called


def test_generar_pdf_desde_payload(client: TestClient):
    from app.dependencies import get_pdf_generator

    class _StubPdf:
        def __init__(self):
            self.received = None

        def build_pdf(self, payload):
            self.received = payload
            return b"%PDF-1.4"

    pdf_stub = _StubPdf()
    app.dependency_overrides[get_pdf_generator] = lambda: pdf_stub

    body = {
        "recomendacion": {
            "lote_id": "lote-prueba",
            "tipo_recomendacion": "siembra",
            "prediccion_id": str(uuid4()),
            "cultivo": "trigo",
            "recomendacion_principal": {
                "fecha_optima": "01-09-2025",
                "ventana": ["30-08-2025", "03-09-2025"],
                "confianza": 0.9,
                "riesgos": []
            },
            "alternativas": [],
            "nivel_confianza": 0.9,
            "costos_estimados": {},
            "fecha_generacion": "2025-01-01T00:00:00Z",
            "datos_entrada": {"campana": "2024/2025"}
        },
        "metadata": {"lote_label": "Lote Test"}
    }

    try:
        response = client.post(
            "/api/v1/recomendaciones/siembra/pdf",
            json=body,
            headers=_auth_headers(),
        )
    finally:
        app.dependency_overrides.pop(get_pdf_generator, None)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert pdf_stub.received is not None
