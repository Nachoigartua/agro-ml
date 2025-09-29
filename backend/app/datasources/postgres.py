from typing import List, Optional
from psycopg2.extensions import connection
from app.datasources.base import DataSource, Campana, Lote, Cultivo, ClimateSummary

class PostgresSource(DataSource):
    def __init__(self, conn: connection):
        self.conn = conn

    # --- Catálogo ---
    def get_campanas(self) -> List[Campana]:
        sql = "SELECT id::text, nombre FROM campanas ORDER BY id;"
        with self.conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return [Campana(id=r[0], nombre=r[1]) for r in rows]

    def get_lotes(self) -> List[Lote]:
        sql = """
        SELECT id::text, nombre, latitud, longitud, hectareas, cultivo_id::text
        FROM lotes
        ORDER BY id;
        """
        with self.conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return [
            Lote(
                id=r[0], nombre=r[1],
                latitud=float(r[2]), longitud=float(r[3]),
                hectareas=float(r[4]), cultivo_id=r[5]
            )
            for r in rows
        ]

    def get_cultivos(self) -> List[Cultivo]:
        sql = "SELECT id::text, nombre, tipo FROM cultivos ORDER BY id;"
        with self.conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return [Cultivo(id=r[0], nombre=r[1], tipo=r[2]) for r in rows]

    # --- Modelos / simulaciones con datos de la DB ---
    def climate_summary(self, lat: float, lon: float, dias: int) -> Optional[ClimateSummary]:
        """
        Busca un resumen simple (media de los últimos 'dias') si existe una tabla 'clima_diario'
        con columnas: fecha, latitud, longitud, temp, precip, humedad, viento, radiacion.
        Si no existe, devuelve None (para que la capa superior maneje fallback lógico).
        """
        with self.conn.cursor() as cur:
            # Verificar existencia de tabla
            cur.execute("""
                SELECT to_regclass('public.clima_diario') IS NOT NULL;
            """)
            exists = cur.fetchone()[0]
            if not exists:
                return None

            # Selección por proximidad simple (±0.05°) y últimos N días
            cur.execute("""
                WITH recent AS (
                  SELECT temp, precip, humedad, viento, radiacion
                  FROM clima_diario
                  WHERE latitud BETWEEN %s-0.05 AND %s+0.05
                    AND longitud BETWEEN %s-0.05 AND %s+0.05
                  ORDER BY fecha DESC
                  LIMIT %s
                )
                SELECT AVG(temp), AVG(precip), AVG(humedad), AVG(viento), AVG(radiacion)
                FROM recent;
            """, (lat, lat, lon, lon, max(7, dias)))
            row = cur.fetchone()
            if row is None or row[0] is None:
                return None
        return ClimateSummary(
            temp_media=float(row[0]), precip=float(row[1] or 0),
            humedad=float(row[2] or 0), viento=float(row[3] or 0),
            radiacion=float(row[4] or 0),
        )

    def historic_yields(self, lote_id: str) -> List[int]:
        """
        Lee rendimientos históricos si existe tabla 'rendimientos' con:
        lote_id, campana_id, rendimiento_kg_ha (int).
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.rendimientos') IS NOT NULL;")
            exists = cur.fetchone()[0]
            if not exists:
                return []
            cur.execute("""
                SELECT rendimiento_kg_ha
                FROM rendimientos
                WHERE lote_id::text = %s
                ORDER BY campana_id DESC
                LIMIT 5;
            """, (lote_id,))
            rows = cur.fetchall()
        return [int(r[0]) for r in rows]

    def soil_mo(self, lote_id: str) -> Optional[float]:
        """
        Lee materia orgánica si existe 'analisis_suelo' con:
        lote_id, fecha, mo_porcentaje (numeric).
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.analisis_suelo') IS NOT NULL;")
            exists = cur.fetchone()[0]
            if not exists:
                return None
            cur.execute("""
                SELECT mo_porcentaje
                FROM analisis_suelo
                WHERE lote_id::text = %s
                ORDER BY fecha DESC
                LIMIT 1;
            """, (lote_id,))
            row = cur.fetchone()
            if not row:
                return None
        return float(row[0])
