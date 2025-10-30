"""SQLAlchemy declarative base class."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class shared by all ORM models."""

    pass
