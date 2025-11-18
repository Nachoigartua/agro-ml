"""Application configuration management."""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Container for environment-driven configuration."""

    def __init__(self) -> None:
        try:
            self.database_url: str = os.environ["DATABASE_URL"]
        except KeyError as exc:  # pragma: no cover - defensive programming
            raise RuntimeError(
                "DATABASE_URL must be defined; configure your environment before starting the app."
            ) from exc


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated environment parsing."""

    return Settings()


settings: Settings = get_settings()


__all__: tuple[str, ...] = ("settings", "get_settings", "Settings")
