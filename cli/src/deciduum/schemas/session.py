"""Session schemas for CLI payload validation."""

from pydantic import BaseModel, Field
from typing import Optional


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    name: Optional[str] = Field(
        None, description="Session name (defaults to session_id if not provided)"
    )
