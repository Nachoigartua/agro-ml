from uuid import uuid4
import pytest

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.dependencies import get_siembra_service  # noqa: E402
from app.dto.siembra import SiembraRequest  # noqa: F401, E402 (type ref only)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_siembra_recommendation_happy_path(client: TestClient):
    # Given: a valid payload for siembra recommendations
    payload = {
        "lote_id": "lote-001",
        "cliente_id": str(uuid4()),
        "cultivo": "trigo",
        "campana": "2024/2025",
        "fecha_consulta": "2024-10-01T00:00:00Z",
    }

    headers = {"Authorization": "Bearer test-token"}

    # When: calling the endpoint
    response = client.post("/api/v1/recomendaciones/siembra", json=payload, headers=headers)

    # Then: it returns 200 and the expected structure
    assert response.status_code == 200
    data = response.json()

    # Basic structure checks per ET guidelines
    assert "recomendacion_principal" in data
    assert "alternativas" in data

    # A couple of light sanity checks on content
    assert data["tipo_recomendacion"] == "siembra"
    assert isinstance(data["alternativas"], list)


def test_siembra_recommendation_invalid_body_returns_422(client: TestClient):
    # Given: an invalid payload (invalid cultivo value)
    payload = {
        "lote_id": "lote-001",
        "cliente_id": str(uuid4()),
        "cultivo": "cultivo_invalido",
        "campana": "2024/2025",
        "fecha_consulta": "2024-10-01T00:00:00Z",
    }

    headers = {"Authorization": "Bearer test-token"}

    # When: calling the endpoint
    response = client.post("/api/v1/recomendaciones/siembra", json=payload, headers=headers)

    # Then: FastAPI/Pydantic returns 422 Unprocessable Entity
    assert response.status_code == 422
    detail = response.json().get("detail", [])
    assert isinstance(detail, list)
    # Check that validation message mentions allowed cultivos
    assert any("cultivo debe ser uno de" in (err.get("msg") or "") for err in detail)
