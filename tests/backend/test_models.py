"""
Tests for ML models
"""
import pytest
import numpy as np
from ml.siembra.model import SiembraModel
from ml.rendimiento.model import RendimientoModel
from ml.variedades.model import VariedadesModel


@pytest.mark.asyncio
async def test_siembra_model_train():
    """Test training siembra model"""
    model = SiembraModel()
    result = await model.train({})
    
    assert result["status"] == "success"
    assert "metrics" in result
    assert model.model is not None


@pytest.mark.asyncio
async def test_siembra_model_predict():
    """Test siembra prediction"""
    model = SiembraModel()
    
    # Train first
    await model.train({})
    
    # Make prediction
    data = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "trigo",
        "campana": "2024/2025"
    }
    
    result = await model.predict(data)
    
    assert result["tipo_prediccion"] == "siembra"
    assert "recomendacion_principal" in result
    assert "nivel_confianza" in result
    assert 0 <= result["nivel_confianza"] <= 1


@pytest.mark.asyncio
async def test_rendimiento_model_predict():
    """Test rendimiento prediction"""
    model = RendimientoModel()
    
    # Train first
    await model.train({})
    
    # Make prediction
    data = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "soja",
        "fecha_siembra": "2024-10-15",
        "variedad": "DM4670"
    }
    
    result = await model.predict(data)
    
    assert result["tipo_prediccion"] == "rendimiento"
    assert "recomendacion_principal" in result
    assert "rendimiento_esperado_kg_ha" in result["recomendacion_principal"]


@pytest.mark.asyncio
async def test_variedades_model_predict():
    """Test variedades prediction"""
    model = VariedadesModel()
    
    # Train first
    await model.train({})
    
    # Make prediction
    data = {
        "lote_id": "lote-001",
        "cliente_id": "cliente-001",
        "cultivo": "trigo",
        "objetivo_productivo": "rendimiento"
    }
    
    result = await model.predict(data)
    
    assert result["tipo_prediccion"] == "variedades"
    assert "recomendacion_principal" in result
    assert "variedad" in result["recomendacion_principal"]


def test_model_save_and_load():
    """Test model persistence"""
    model = SiembraModel()
    
    # Create dummy model
    from sklearn.ensemble import RandomForestRegressor
    model.model = RandomForestRegressor(n_estimators=10)
    model.metadata = {
        "trained_at": "2024-01-01",
        "version": "1.0.0"
    }
    
    # Save
    model.save_model()
    
    # Create new instance and load
    new_model = SiembraModel()
    loaded = new_model.load_model()
    
    assert loaded == True
    assert new_model.model is not None
    assert new_model.metadata["version"] == "1.0.0"