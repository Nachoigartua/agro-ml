from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .controllers.recommendations_controller import router as recommendations_router
from .middleware.auth import AuthMiddleware


app = FastAPI(
    title="Agro ML API",
    version="1.0.0",
    description="API para recomendaciones agronomicas",
)

# CORS: habilitar preflight y permitir origen del frontend (desarrollo, luego se usa nginx para prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # incluye Authorization y Content-Type
)

# Registrar middleware de autenticación para propagar el token
app.add_middleware(AuthMiddleware)

app.include_router(recommendations_router)
