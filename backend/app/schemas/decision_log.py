from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# DecisionLog Schemas
class DecisionLogBase(BaseModel):
    type: str = Field(..., pattern="^(note|reflection|state_change)$")
    content: str = Field(..., min_length=1, max_length=10000)


class DecisionLogCreate(DecisionLogBase):
    pass


class DecisionLogResponse(DecisionLogBase):
    id: str
    decision_id: str
    created_at: datetime

    class Config:
        from_attributes = True
