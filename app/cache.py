import json,redis,hashlib
from typing import Optional
from .config import settings
_r=None
TTL_BY_TYPE={'siembra':604800,'variedades':2592000,'rendimiento':2592000,'clima':86400,'fertilizacion':1296000,'agroquimicos':1296000,'cosecha':1296000}

def get_redis():
  global _r
  if _r is None:
    _r=redis.Redis(host=settings.REDIS_HOST,port=settings.REDIS_PORT,decode_responses=True)
  return _r

def make_cache_key(kind,payload):
  import json,hashlib
  return f"{kind}:{hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}"

def cache_get(key)->Optional[dict]:
  r=get_redis(); raw=r.get(key)
  return json.loads(raw) if raw else None

def cache_set(key,value,ttl:int):
  r=get_redis(); r.set(key,json.dumps(value),ex=ttl)
