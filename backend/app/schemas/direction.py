from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Direction Schemas
class DirectionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class DirectionCreate(DirectionBase):
    pass


class DirectionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)


class DirectionResponse(DirectionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    decision_count: int = 0

    class Config:
        from_attributes = True


class DirectionWithDetails(DirectionResponse):
    decisions: list = []
    memos: list = []
