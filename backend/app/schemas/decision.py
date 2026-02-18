from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# Decision Schemas
class DecisionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    status: str = Field(default="ongoing", pattern="^(completed|ongoing|archived)$")
    review_at: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    direction_id: Optional[str] = None


class DecisionCreate(DecisionBase):
    pass


class DecisionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Optional[str] = Field(None, pattern="^(completed|ongoing|archived)$")
    review_at: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    direction_id: Optional[str] = None


class DecisionResponse(DecisionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
