from fastapi import Request, HTTPException, Header
from .config import settings
from .cache import get_redis

def api_key_checker(x_api_key: str | None = Header(default=None)):
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')

def rate_limiter(request: Request):
    r = get_redis()
    ip = request.headers.get('x-forwarded-for') or request.client.host
    key = f'ratelimit:{ip}:{request.url.path}'
    c = r.incr(key)
    if c == 1:
        r.expire(key, 60)
    if c > 60:
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
