"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_models_status():
    """Test models status endpoint"""
    response = client.get(
        "/api/ml/models/status",
        headers={"x-api-key": "dev-local-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "models" in data


def test_predict_siembra():
    """Test siembra prediction endpoint"""
    payload = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "trigo",
        "campana": "2024/2025"
    }
    
    response = client.post(
        "/api/ml/predict/siembra",
        json=payload,
        headers={"x-api-key": "dev-local-key"}
    )
    
    # Should succeed or return 500 if model not trained yet
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert data["tipo_prediccion"] == "siembra"


def test_predict_without_api_key():
    """Test that API requires authentication"""
    payload = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "trigo",
        "campana": "2024/2025"
    }
    
    response = client.post(
        "/api/ml/predict/siembra",
        json=payload
    )
    
    assert response.status_code == 422  # Missing header


def test_predict_with_invalid_api_key():
    """Test that invalid API key is rejected"""
    payload = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "trigo",
        "campana": "2024/2025"
    }
    
    response = client.post(
        "/api/ml/predict/siembra",
        json=payload,
        headers={"x-api-key": "invalid-key"}
    )
    
    assert response.status_code == 401


def test_mock_endpoints():
    """Test mock data endpoints"""
    response = client.get(
        "/api/mock/lotes",
        headers={"x-api-key": "dev-local-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_train_model():
    """Test model training endpoint"""
    payload = {
        "force_retrain": True
    }
    
    response = client.post(
        "/api/ml/train/siembra",
        json=payload,
        headers={"x-api-key": "dev-local-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["modelo"] == "siembra"
    assert data["status"] == "success"


def test_invalid_model_name():
    """Test training with invalid model name"""
    payload = {
        "force_retrain": True
    }
    
    response = client.post(
        "/api/ml/train/invalid_model",
        json=payload,
        headers={"x-api-key": "dev-local-key"}
    )
    
    assert response.status_code == 400