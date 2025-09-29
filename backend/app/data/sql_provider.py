import json
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Float, DateTime, create_engine, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func, select
from .provider import DataProvider

Base = declarative_base()

class Lote(Base):
    __tablename__ = "lotes"
    id = Column(String, primary_key=True)
    cliente_id = Column(String, index=True)
    nombre = Column(String)
    superficie_ha = Column(Float)
    # Polígono en WKT para simplificar local
    geom_wkt = Column(Text)

class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"
    id = Column(String, primary_key=True)
    lote_id = Column(String, index=True)
    tipo_labor = Column(String)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    insumos_json = Column(Text)  # JSON serializado
    dosis = Column(Float)

class Cosecha(Base):
    __tablename__ = "cosechas"
    id = Column(String, primary_key=True)
    lote_id = Column(String, index=True)
    cultivo = Column(String)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    cantidad_cosechada = Column(Float)
    calidad_json = Column(Text)

class SQLDataProvider(DataProvider):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        # Seed opcional desde JSON (simulación de BD), nunca hardcoded en código
        seed_path = os.path.join(os.path.dirname(__file__), "seed.json")
        self._ensure_seed(seed_path)

    def _ensure_seed(self, seed_path: str):
        with self.engine.begin() as conn:
            lotes_count = conn.execute(select(func.count()).select_from(Lote)).scalar_one()
            if lotes_count and lotes_count > 0:
                return
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self.engine.begin() as conn:
                for l in data.get("lotes", []):
                    conn.execute(
                        Lote.__table__.insert().values(**l)
                    )
                for o in data.get("ordenes_trabajo", []):
                    conn.execute(
                        OrdenTrabajo.__table__.insert().values(**o)
                    )
                for c in data.get("cosechas", []):
                    conn.execute(
                        Cosecha.__table__.insert().values(**c)
                    )

    async def get_lotes(self, cliente_id: str) -> List[Dict[str, Any]]:
        with self.SessionLocal() as s:
            rows = s.query(Lote).filter(Lote.cliente_id == cliente_id).all()
            return [dict(id=r.id, cliente_id=r.cliente_id, nombre=r.nombre, superficie_ha=r.superficie_ha, geom_wkt=r.geom_wkt) for r in rows]

    async def get_lote(self, lote_id: str) -> Optional[Dict[str, Any]]:
        with self.SessionLocal() as s:
            r = s.query(Lote).filter(Lote.id == lote_id).first()
            return dict(id=r.id, cliente_id=r.cliente_id, nombre=r.nombre, superficie_ha=r.superficie_ha, geom_wkt=r.geom_wkt) if r else None

    async def get_ordenes_trabajo(self, lote_id: str, fecha_desde: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.SessionLocal() as s:
            q = s.query(OrdenTrabajo).filter(OrdenTrabajo.lote_id == lote_id)
            rows = q.all()
            return [dict(id=r.id, lote_id=r.lote_id, tipo_labor=r.tipo_labor, fecha=str(r.fecha), insumos_json=r.insumos_json, dosis=r.dosis) for r in rows]

    async def get_cosechas_historicas(self, lote_id: str) -> List[Dict[str, Any]]:
        with self.SessionLocal() as s:
            rows = s.query(Cosecha).filter(Cosecha.lote_id == lote_id).all()
            return [dict(id=r.id, lote_id=r.lote_id, cultivo=r.cultivo, fecha=str(r.fecha), cantidad_cosechada=r.cantidad_cosechada, calidad_json=r.calidad_json) for r in rows]

    async def validate_token(self, token: str) -> Dict[str, Any]:
        # Simulación: acepta cualquier token no vacío en entornos de desarrollo
        if token and token.strip():
            return {"valid": True, "user_info": {"sub": "dev-user"}}
        return {"valid": False}
