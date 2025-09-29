from cachetools import TTLCache

# TTLs por tipo de dato (segundos)
TTL_BY_TYPE = {
    "catalog": 3600,
    "climate_summary": 900,
    "soil": 1800,
}

_caches = {}

def cache_for(key: str) -> TTLCache:
    ttl = TTL_BY_TYPE.get(key, 600)
    if key not in _caches:
        _caches[key] = TTLCache(maxsize=512, ttl=ttl)
    return _caches[key]
