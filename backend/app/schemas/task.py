from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed)$")
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = None
    decision_id: str


class TaskCreate(TaskBase):
    decision_id: Optional[str] = None  # Optional - can be provided but not required


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = None
    decision_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    due_date: Optional[str]
    notes: Optional[str]
    decision_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
