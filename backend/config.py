"""
Configuration management using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # API
    API_KEY: str = Field(default="dev-local-key", env="API_KEY")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:4200", "http://localhost:8080", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://agro_user:agro_password@postgres:5432/agro_ml",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    PREDICTION_CACHE_TTL_HOURS: int = Field(default=24, env="PREDICTION_CACHE_TTL_HOURS")
    
    # Finnegans Integration
    FINNEGANS_API_URL: str = Field(
        default="http://finnegans-mock:8001",
        env="FINNEGANS_API_URL"
    )
    FINNEGANS_API_KEY: str = Field(default="mock-key", env="FINNEGANS_API_KEY")
    USE_MOCK_DATA: bool = Field(default=True, env="USE_MOCK_DATA")
    
    # ML Models
    MODEL_RETRAIN_INTERVAL_DAYS: int = Field(default=90, env="MODEL_RETRAIN_INTERVAL_DAYS")
    ML_MODELS_PATH: str = Field(default="/app/ml_models", env="ML_MODELS_PATH")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()