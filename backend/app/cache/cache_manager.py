import json
from datetime import timedelta
from typing import Any, Dict, Optional
import redis

class IntelligentCache:
    def __init__(self):
        # TTL en horas por tipo de predicción (alineado al ET)
        self.cache_strategies = {
            "siembra": {"ttl": 7*24, "invalidate_on": ["weather_update"]},
            "rendimiento": {"ttl": 30*24, "invalidate_on": ["harvest_data"]},
            "clima": {"ttl": 24, "invalidate_on": ["weather_api_update"]},
        }

    def get_cache_key(self, prediction_type: str, params: Dict[str, Any]) -> str:
        relevant = tuple(sorted((k, str(v)) for k, v in params.items()))
        return f"{prediction_type}:{hash(relevant)}"

    def get_ttl(self, prediction_type: str) -> int:
        return self.cache_strategies.get(prediction_type, {"ttl": 24}).get("ttl", 24)

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.strategy = IntelligentCache()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self.redis.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, payload: Dict[str, Any], ttl_hours: int):
        self.redis.setex(key, timedelta(hours=ttl_hours), json.dumps(payload))
