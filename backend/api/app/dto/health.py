from __future__ import annotations

from pydantic import BaseModel, Field


class HealthStatusResponse(BaseModel):
    status: str = Field(default="ok")
