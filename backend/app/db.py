import time
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from .config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    DB_POOL_MIN,
    DB_POOL_MAX,
    DB_CONN_TIMEOUT,
)

_pool: Optional[SimpleConnectionPool] = None


def _dsn() -> str:
    # connect_timeout evita que uvicorn quede colgado si DB no responde
    return (
        f"dbname={POSTGRES_DB} "
        f"user={POSTGRES_USER} "
        f"password={POSTGRES_PASSWORD} "
        f"host={POSTGRES_HOST} "
        f"port={POSTGRES_PORT} "
        f"connect_timeout={DB_CONN_TIMEOUT}"
    )


def init_pool() -> SimpleConnectionPool:
    """
    Crea el pool la primera vez que se usa. No tocar en import-time.
    """
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(DB_POOL_MIN, DB_POOL_MAX, dsn=_dsn())
    return _pool


@contextmanager
def get_db_cursor() -> Generator:
    """
    Context manager para obtener cursor y hacer commit/cleanup seguro.
    Uso:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1")
    """
    pool = init_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    finally:
        pool.putconn(conn)


def ping() -> None:
    """
    Lanza excepción si no puede ejecutar SELECT 1.
    Útil para healthchecks o verificación en startup.
    """
    with get_db_cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
