"""Direction schemas for CLI payload validation."""

from pydantic import BaseModel, Field
from typing import Optional


class DirectionCreate(BaseModel):
    """Schema for creating a new direction."""

    title: str = Field(..., description="Direction title (required)")


class DirectionUpdate(BaseModel):
    """Schema for updating an existing direction."""

    title: Optional[str] = Field(None, description="Direction title")
