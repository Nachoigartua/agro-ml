import os

class Config:
    # Permite tanto DB_* como POSTGRES_* para evitar desalineos entre compose/código
    DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "db")
    DB_PORT = int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "mlagrico")
    DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "ml_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "ml_password")

    DATASOURCE = os.getenv("DATASOURCE", "postgres")  # 'postgres' | 'finnegans'
    FIN_URL = os.getenv("FIN_URL", "")
    FIN_API_KEY = os.getenv("FIN_API_KEY", "")

    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")

CFG = Config()
