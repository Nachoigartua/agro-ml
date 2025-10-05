from fastapi import FastAPI

from .controllers.recommendations_controller import router as recommendations_router
from .middleware.auth import AuthMiddleware


app = FastAPI(
    title="Agro ML API",
    version="1.0.0",
    description="API para recomendaciones agronomicas"
)

# Registrar middleware de autenticación para propagar el token
app.add_middleware(AuthMiddleware)

app.include_router(recommendations_router)

