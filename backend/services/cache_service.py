"""
Redis cache service for predictions
"""
import redis.asyncio as redis
import json
from typing import Any, Optional
from datetime import timedelta
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """Service for caching predictions in Redis"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = timedelta(hours=settings.PREDICTION_CACHE_TTL_HOURS)
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Conectado a Redis exitosamente")
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Desconectado de Redis")
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis ping falló: {e}")
            return False
    
    async def get_cached_prediction(self, cache_key: str) -> Optional[dict]:
        """Get cached prediction"""
        try:
            if not self.redis_client:
                await self.connect()
            
            if not self.redis_client:
                return None
            
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
            
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo de cache: {e}")
            return None
    
    async def cache_prediction(
        self, 
        cache_key: str, 
        prediction: dict, 
        ttl: Optional[timedelta] = None
    ):
        """Cache a prediction"""
        try:
            if not self.redis_client:
                await self.connect()
            
            if not self.redis_client:
                return
            
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())
            
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(prediction, default=str)
            )
            logger.debug(f"Cached: {cache_key} (TTL: {ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"Error guardando en cache: {e}")
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            if not self.redis_client:
                await self.connect()
            
            if not self.redis_client:
                return
            
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidadas {len(keys)} entradas de cache")
            
        except Exception as e:
            logger.error(f"Error invalidando cache: {e}")
    
    def generate_cache_key(self, prediction_type: str, params: dict) -> str:
        """Generate cache key for prediction"""
        # Ordenar params para consistencia
        sorted_params = sorted(params.items())
        params_str = "_".join([f"{k}:{v}" for k, v in sorted_params])
        return f"prediction:{prediction_type}:{params_str}"


# Global cache service instance
cache_service = CacheService()