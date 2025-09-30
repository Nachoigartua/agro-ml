"""
Database repositories for data access
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from database.connection import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


class PredictionRepository:
    """Repository for predictions data"""
    
    async def save_prediction(self, prediction: Dict[str, Any]) -> str:
        """Save a prediction to the database"""
        try:
            pool = await get_db_connection()
            
            async with pool.acquire() as conn:
                prediction_id = await conn.fetchval(
                    """
                    INSERT INTO predicciones (
                        lote_id,
                        cliente_id,
                        tipo_prediccion,
                        cultivo,
                        fecha_creacion,
                        recomendacion_principal,
                        alternativas,
                        nivel_confianza,
                        datos_entrada,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    prediction.get("lote_id"),
                    prediction.get("metadata", {}).get("cliente_id"),
                    prediction.get("tipo_prediccion"),
                    prediction.get("metadata", {}).get("cultivo"),
                    datetime.utcnow(),
                    json.dumps(prediction.get("recomendacion_principal", {})),
                    json.dumps(prediction.get("alternativas", [])),
                    prediction.get("nivel_confianza", 0.0),
                    json.dumps(prediction.get("metadata", {})),
                    json.dumps(prediction.get("metadata", {}))
                )
            
            logger.info(f"Predicción guardada con ID: {prediction_id}")
            return str(prediction_id)
            
        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")
            raise
    
    async def get_prediction_by_id(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """Get a prediction by ID"""
        try:
            pool = await get_db_connection()
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM predicciones WHERE id = $1
                    """,
                    prediction_id
                )
            
            if not row:
                return None
            
            return dict(row)
            
        except Exception as e:
            logger.error(f"Error obteniendo predicción: {e}")
            return None
    
    async def get_predictions_by_lote(
        self, 
        lote_id: str,
        tipo_prediccion: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all predictions for a lote"""
        try:
            pool = await get_db_connection()
            
            query = "SELECT * FROM predicciones WHERE lote_id = $1"
            params = [lote_id]
            
            if tipo_prediccion:
                query += " AND tipo_prediccion = $2"
                params.append(tipo_prediccion)
            
            query += " ORDER BY fecha_creacion DESC LIMIT 50"
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error obteniendo predicciones por lote: {e}")
            return []
    
    async def delete_old_predictions(self, days: int = 90):
        """Delete predictions older than specified days"""
        try:
            pool = await get_db_connection()
            
            async with pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM predicciones 
                    WHERE fecha_creacion < NOW() - INTERVAL '%s days'
                    """,
                    days
                )
            
            logger.info(f"Predicciones antiguas eliminadas: {result}")
            
        except Exception as e:
            logger.error(f"Error eliminando predicciones antiguas: {e}")


class ModelRepository:
    """Repository for ML models metadata"""
    
    async def save_model_metadata(self, model_data: Dict[str, Any]) -> str:
        """Save model metadata to database"""
        try:
            pool = await get_db_connection()
            
            async with pool.acquire() as conn:
                model_id = await conn.fetchval(
                    """
                    INSERT INTO modelos_ml (
                        nombre,
                        version,
                        tipo_modelo,
                        metricas_performance,
                        fecha_entrenamiento,
                        activo
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    model_data.get("nombre"),
                    model_data.get("version"),
                    model_data.get("tipo_modelo"),
                    json.dumps(model_data.get("metricas", {})),
                    datetime.utcnow(),
                    True
                )
            
            logger.info(f"Metadata de modelo guardada con ID: {model_id}")
            return str(model_id)
            
        except Exception as e:
            logger.error(f"Error guardando metadata de modelo: {e}")
            raise