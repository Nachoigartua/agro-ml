from fastapi import FastAPI

from .controllers.recommendations_controller import router as recommendations_router


app = FastAPI(
    title="Agro ML API",
    version="1.0.0",
    description="API para recomendaciones agronomicas"
)

app.include_router(recommendations_router)
