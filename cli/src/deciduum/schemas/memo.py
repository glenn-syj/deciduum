"""Memo schemas for CLI payload validation."""

from pydantic import BaseModel, Field
from typing import Optional


class MemoCreate(BaseModel):
    """Schema for creating a new memo."""

    content: str = Field(..., description="Memo content (required)")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    linked_decision_id: Optional[str] = Field(None, description="Linked decision ID")
    linked_direction_id: Optional[str] = Field(None, description="Linked direction ID")


class MemoUpdate(BaseModel):
    """Schema for updating an existing memo."""

    content: Optional[str] = Field(None, description="Memo content")
    linked_decision_id: Optional[str] = Field(None, description="Linked decision ID")
    linked_direction_id: Optional[str] = Field(None, description="Linked direction ID")
