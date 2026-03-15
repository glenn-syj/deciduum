"""Task schemas for CLI payload validation."""

from pydantic import BaseModel, Field
from typing import Optional


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(..., description="Task title (required)")
    decision_id: str = Field(..., description="Associated decision ID (required)")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    notes: Optional[str] = Field(None, description="Task notes")
    status: str = Field("pending", description="Task status")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(None, description="Task title")
    status: Optional[str] = Field(None, description="Task status")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    notes: Optional[str] = Field(None, description="Task notes")
