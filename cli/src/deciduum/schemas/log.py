"""Log schemas for CLI payload validation."""

from pydantic import BaseModel, Field


class LogCreate(BaseModel):
    """Schema for creating a new decision log entry."""

    decision_id: str = Field(..., description="Associated decision ID (required)")
    type: str = Field(
        ..., description="Log type: note, reflection, or state_change (required)"
    )
    content: str = Field(..., description="Log content (required)")
    source: str = Field("human", description="Log source (default: human)")
