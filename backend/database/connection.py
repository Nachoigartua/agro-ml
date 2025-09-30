"""
Database connection management
"""
import asyncpg
from typing import Optional
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool"""
    global _pool
    
    try:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Pool de conexiones a la base de datos creado")
        
        async with _pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            logger.info(f"Conectado a PostgreSQL: {version}")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


async def close_db():
    """Close database connection pool"""
    global _pool
    
    if _pool:
        await _pool.close()
        logger.info("Pool de conexiones cerrado")
        _pool = None


async def get_db_connection():
    """Get a database connection from the pool"""
    global _pool
    
    if not _pool:
        await init_db()
    
    return _pool


async def check_db_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        global _pool
        if not _pool:
            return False
        
        async with _pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False