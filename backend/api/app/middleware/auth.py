"""Middleware de autenticación para la aplicación."""
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger

logger = get_logger("auth")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validar token del sistema principal
        token = request.headers.get("Authorization")
        if not token:
            logger.warning(
                "Intento de acceso sin token de autorización",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_host": request.client.host if request.client else "unknown",
                }
            )
            # En producción, esto debería retornar un 401 y logear la excepción
            # Por ahora, permitimos requests sin token para desarrollo
            request.state.user = None
            return await call_next(request)

        # TODO: Implementar validación real con el sistema principal
        # Por ahora solo guardamos el token
        request.state.user = {"token": token}
        return await call_next(request)