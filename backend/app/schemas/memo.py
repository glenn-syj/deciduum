from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Memo Schemas
class MemoBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    linked_decision_id: Optional[str] = None
    linked_direction_id: Optional[str] = None


class MemoCreate(MemoBase):
    pass


class MemoUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    linked_decision_id: Optional[str] = None
    linked_direction_id: Optional[str] = None


class MemoResponse(MemoBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
