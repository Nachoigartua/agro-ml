"""
Authentication middleware
"""
from fastapi import HTTPException, Header
from config import settings


async def verify_api_key(x_api_key: str = Header(...)):
    """
    Verifica que el API key sea válido
    """
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API key inválida"
        )
    return x_api_key