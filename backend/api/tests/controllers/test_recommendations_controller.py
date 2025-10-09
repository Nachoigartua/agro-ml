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
    payload = {
        "lote_id": "lote-001",
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

    # Validaciones de campos de alto nivel
    assert data["lote_id"] == payload["lote_id"]
    assert data["tipo_recomendacion"] == "siembra"
    assert data["cultivo"] == payload["cultivo"]

    # Validaciones de la recomendacion principal (nuevo esquema)
    rp = data.get("recomendacion_principal", {})
    assert isinstance(rp, dict)
    assert "fecha_optima" in rp
    assert "ventana" in rp
    assert "confianza" in rp

    from datetime import datetime as _dt

    # La fecha optima debe pertenecer al año siguiente al de la consulta
    fecha_optima = rp["fecha_optima"]
    dt = _dt.strptime(fecha_optima, "%d-%m-%Y")
    assert dt.year == 2025  # fecha consulta 2024 -> recomienda 2025


def test_siembra_recommendation_invalid_body_returns_422(client: TestClient):
    payload = {
        "lote_id": "lote-001",
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
