import os

# Config simple, sin dependencias extra
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mlagrico")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ml_user")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secret")
# Dentro de docker, el host por defecto debe ser el nombre del servicio: "db"
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

# Pool y timeouts
DB_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "10"))
DB_CONN_TIMEOUT: int = int(os.getenv("DB_CONN_TIMEOUT", "5"))
DB_STARTUP_MAX_RETRIES: int = int(os.getenv("DB_STARTUP_MAX_RETRIES", "30"))
DB_STARTUP_BACKOFF_SECS: float = float(os.getenv("DB_STARTUP_BACKOFF_SECS", "1.0"))
