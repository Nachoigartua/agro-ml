import time
import psycopg2
from contextlib import contextmanager
from typing import Optional
from app.config import CFG

_conn = None  # conexión perezosa única

def _connect_once() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        dbname=CFG.DB_NAME,
        user=CFG.DB_USER,
        password=CFG.DB_PASSWORD,
        host=CFG.DB_HOST,
        port=CFG.DB_PORT,
    )
    conn.autocommit = True
    return conn

def get_conn() -> psycopg2.extensions.connection:
    """Conecta perezosamente con reintentos; evita caerse si DB aún no está o hay jitter."""
    global _conn
    if _conn is not None and not _conn.closed:
        return _conn

    last_err: Optional[Exception] = None
    for _ in range(30):  # ~30s
        try:
            _conn = _connect_once()
            # sanity check
            with _conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            return _conn
        except Exception as e:
            last_err = e
            time.sleep(1)

    raise last_err if last_err else RuntimeError("No se pudo conectar a Postgres")

@contextmanager
def get_db_cursor():
    """Compat con código que espera un cursor por contexto."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
