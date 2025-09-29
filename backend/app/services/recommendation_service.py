from typing import Dict, Any
from ..models.ml_models import SiembraPredictor
from ..cache.cache_manager import CacheManager

class RecommendationService:
    def __init__(self, cache: CacheManager):
        self.predictor = SiembraPredictor()
        self.cache = cache

    async def siembra(self, features: Dict[str, Any]) -> Dict[str, Any]:
        # Cache inteligente
        from ..cache.cache_manager import IntelligentCache
        strategy = IntelligentCache()
        key = strategy.get_cache_key("siembra", features)
        cached = self.cache.get(key)
        if cached:
            return cached

        result = self.predictor.predict(features)
        payload = {
            "recomendacion_principal": f"Sembrar {features['cultivo']} en fecha óptima",
            **result,
        }
        self.cache.set(key, payload, strategy.get_ttl("siembra"))
        return payload
