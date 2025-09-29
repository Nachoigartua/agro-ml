from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timedelta
import psycopg2
from .db import get_conn

class CatalogRepository:
    def get_lotes(self) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""SELECT id::text, nombre, latitud, longitud FROM lotes ORDER BY nombre""")
            rows = cur.fetchall()
            return [{"id": r[0], "nombre": r[1], "latitud": float(r[2]), "longitud": float(r[3])} for r in rows]

    def get_campanas(self) -> List[Dict[str, Any]]:
        # explicit table to allow clients to customize later
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""SELECT nombre FROM campanas ORDER BY nombre""")
            return [{"nombre": r[0]} for r in cur.fetchall()]

    def get_cultivos(self) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""SELECT nombre FROM cultivos ORDER BY nombre""")
            return [{"nombre": r[0]} for r in cur.fetchall()]

class ClimaRepository:
    def get_7d_aggregates(self, lat: float, lon: float) -> Optional[Dict[str, float]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    AVG((temperatura_max + temperatura_min)/2.0) AS temp_media,
                    AVG(precipitacion) AS precip,
                    AVG(humedad_relativa) AS humedad,
                    AVG(velocidad_viento) AS viento,
                    AVG(radiacion_solar) AS radiacion
                FROM clima_historico
                WHERE round(latitud::numeric,2)=round(%s::numeric,2)
                  AND round(longitud::numeric,2)=round(%s::numeric,2)
                  AND fecha >= CURRENT_DATE - INTERVAL '7 days'
                """,
                (lat, lon),
            )
            row = cur.fetchone()
            if not row or row[0] is None:
                return None
            return {
                "temp_media": float(row[0]),
                "precip": float(row[1]),
                "humedad": float(row[2]),
                "viento": float(row[3]),
                "radiacion": float(row[4]),
            }

class SueloRepository:
    def get_caracteristicas(self, lote_id: str) -> Optional[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT materia_organica, ph, cec FROM caracteristicas_suelo
                      WHERE lote_id=%s ORDER BY fecha DESC, id DESC LIMIT 1""", (lote_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"materia_organica": float(row[0]), "ph": float(row[1]), "cec": float(row[2])}

class VariedadesRepository:
    def list_by_cultivo(self, cultivo: str) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT variedad, madurez, rendimiento_base_kg_ha,
                              coalesce(tolerancias::text,'{}') as tolerancias, justificacion
                       FROM variedades_catalogo
                       WHERE lower(cultivo)=lower(%s)
                       ORDER BY rendimiento_base_kg_ha DESC""",
                (cultivo,),
            )
            rows = cur.fetchall()
            res = []
            for v, mad, rend, tol_json, just in rows:
                try:
                    import json as _json
                    toler = _json.loads(tol_json)
                except Exception:
                    toler = {}
                res.append({
                    "nombre": v,
                    "madurez": mad,
                    "rendimiento_base_kg_ha": float(rend),
                    "tolerancias": toler,
                    "justificacion": just,
                })
            return res
