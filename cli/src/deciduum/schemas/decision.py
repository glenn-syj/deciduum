"""Decision schemas for CLI payload validation."""

from pydantic import BaseModel, Field
from typing import Optional


class DecisionCreate(BaseModel):
    """Schema for creating a new decision."""

    title: str = Field(..., description="Decision title (required)")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    status: str = Field("ongoing", description="Decision status")
    direction_id: Optional[str] = Field(None, description="Linked direction ID")
    review_at: Optional[str] = Field(
        None, description="Review date in YYYY-MM-DD format"
    )


class DecisionUpdate(BaseModel):
    """Schema for updating an existing decision."""

    title: Optional[str] = Field(None, description="Decision title")
    status: Optional[str] = Field(None, description="Decision status")
    direction_id: Optional[str] = Field(None, description="Linked direction ID")
    review_at: Optional[str] = Field(
        None, description="Review date in YYYY-MM-DD format"
    )
