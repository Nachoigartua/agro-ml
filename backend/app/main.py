from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import CFG
from app.db import get_conn
from app.datasources.base import DataSource, Campana, Cultivo, Lote
from app.datasources.finnegans import FinAPISource
from app.datasources.postgres import PostgresSource

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agro-ml")

# ---- App & CORS ----
app = FastAPI(title="Agro ML API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CFG.CORS_ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Rate limiting ----
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})

# ---- Request/Response models ----
class Coordinates(BaseModel):
    latitud: float
    longitud: float

class ClimaRequest(BaseModel):
    coords: Coordinates
    dias: int = 7

class RendimientoRequest(BaseModel):
    lote_id: str

class SiembraRequest(BaseModel):
    lote_id: str

class VariedadesRequest(BaseModel):
    lote_id: str

class ClimateSummary(BaseModel):
    temp_media: float
    precip: float
    humedad: float
    viento: float
    radiacion: float

class SiembraRecomendacion(BaseModel):
    densidad_plantas_ha: int
    profundidad_cm: int
    observaciones: Optional[str] = None

class VariedadRecomendacion(BaseModel):
    variedad: str
    razon: str

class FertilizacionPlan(BaseModel):
    n_kg_ha: int
    p_kg_ha: int
    k_kg_ha: int
    observaciones: Optional[str] = None

class RendimientoPrediccion(BaseModel):
    rendimiento_kg_ha: int
    intervalo_confianza_kg_ha: List[int]

# ---- DataSource factory ----
def get_datasource() -> DataSource:
    ds = CFG.DATASOURCE.lower()
    if ds == "postgres":
        return PostgresSource(get_conn())
    elif ds == "finnegans":
        return FinAPISource(CFG.FIN_URL, CFG.FIN_API_KEY)
    raise RuntimeError(f"Unknown DATASOURCE={CFG.DATASOURCE}")

# ---- Catálogo ----
@app.get("/api/v1/catalogo/campanas", response_model=List[Campana])
@limiter.limit("30/minute")
def catalogo_campanas(ds: DataSource = Depends(get_datasource)):
    return ds.get_campanas()

@app.get("/api/v1/catalogo/lotes", response_model=List[Lote])
@limiter.limit("30/minute")
def catalogo_lotes(ds: DataSource = Depends(get_datasource)):
    return ds.get_lotes()

@app.get("/api/v1/catalogo/cultivos", response_model=List[Cultivo])
@limiter.limit("30/minute")
def catalogo_cultivos(ds: DataSource = Depends(get_datasource)):
    return ds.get_cultivos()

# ---- Predicciones & Recomendaciones ----
@app.post("/api/v1/predicciones/clima", response_model=ClimateSummary)
@limiter.limit("30/minute")
def prediccion_clima(body: ClimaRequest, ds: DataSource = Depends(get_datasource)):
    c = ds.climate_summary(body.coords.latitud, body.coords.longitud, body.dias)
    if c is None:
        raise HTTPException(404, "Sin datos climáticos para esa ubicación.")
    return c

@app.post("/api/v1/predicciones/rendimiento", response_model=RendimientoPrediccion)
@limiter.limit("20/minute")
def prediccion_rendimiento(body: RendimientoRequest, ds: DataSource = Depends(get_datasource)):
    lotes = {l.id: l for l in ds.get_lotes()}
    lote = lotes.get(body.lote_id)
    yields = ds.historic_yields(body.lote_id)
    base = int(sum(yields) / len(yields)) if yields else 6000
    adj = 0
    if lote:
        clima = ds.climate_summary(lote.latitud, lote.longitud, 7)
        if clima:
            adj += int((22 - abs(clima.temp_media - 22)) * 50)
            adj -= int(min(clima.viento, 40) * 10)
            adj += int(min(clima.radiacion, 25) * 20)
    y = max(3000, base + adj)
    return RendimientoPrediccion(rendimiento_kg_ha=y, intervalo_confianza_kg_ha=[int(y*0.9), int(y*1.1)])

@app.post("/api/v1/recomendaciones/siembra", response_model=SiembraRecomendacion)
@limiter.limit("20/minute")
def recomendaciones_siembra(body: SiembraRequest, ds: DataSource = Depends(get_datasource)):
    lotes = {l.id: l for l in ds.get_lotes()}
    lote = lotes.get(body.lote_id)
    if not lote:
        raise HTTPException(404, "Lote no encontrado")
    clima = ds.climate_summary(lote.latitud, lote.longitud, 14)
    densidad = 65000
    profundidad = 5
    obs = []
    if clima:
        if clima.precip < 5:
            profundidad += 1
            obs.append("Baja precipitación reciente: aumentar 1 cm la profundidad.")
        if clima.humedad < 40:
            densidad -= 5000
            obs.append("Humedad relativa baja: reducir densidad 5k pl/ha.")
        if clima.temp_media < 15:
            obs.append("Temperatura fresca: considerar fecha de siembra más tardía.")
    return SiembraRecomendacion(densidad_plantas_ha=densidad, profundidad_cm=profundidad, observaciones=" ".join(obs) or None)

@app.post("/api/v1/recomendaciones/variedades", response_model=List[VariedadRecomendacion])
@limiter.limit("20/minute")
def recomendaciones_variedades(body: VariedadesRequest, ds: DataSource = Depends(get_datasource)):
    lotes = {l.id: l for l in ds.get_lotes()}
    lote = lotes.get(body.lote_id)
    if not lote:
        raise HTTPException(404, "Lote no encontrado")
    clima = ds.climate_summary(lote.latitud, lote.longitud, 30)
    out: List[VariedadRecomendacion] = []
    if not clima:
        out.append(VariedadRecomendacion(variedad="Híbrido Templado 120", razon="Selección base sin clima."))
        return out
    if clima.precip >= 15 and clima.humedad >= 50:
        out.append(VariedadRecomendacion(variedad="Alto Potencial 125", razon="Alta precipitación y buena humedad."))
    if clima.temp_media >= 24:
        out.append(VariedadRecomendacion(variedad="Ciclo Corto 110", razon="Temp. media elevada."))
    if clima.viento >= 20:
        out.append(VariedadRecomendacion(variedad="Tallo Firme 118", razon="Vientos intensos en la zona."))
    if not out:
        out.append(VariedadRecomendacion(variedad="Equilibrado 115", razon="Condiciones balanceadas."))
    return out

@app.post("/api/v1/optimizacion/fertilizacion", response_model=FertilizacionPlan)
@limiter.limit("10/minute")
def optimizacion_fertilizacion(body: SiembraRequest, ds: DataSource = Depends(get_datasource)):
    mo = ds.soil_mo(body.lote_id)
    if mo is None:
        mo = 2.0
    n = 140 - int((mo - 2.0) * 15)
    p = 40
    k = 30
    n = max(80, n)
    return FertilizacionPlan(n_kg_ha=n, p_kg_ha=p, k_kg_ha=k, observaciones=f"MO={mo:.1f}%. Ajustar con análisis real.")

@app.get("/health")
def health():
    return {"ok": True}
