from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime


# DecisionLog Schemas
class DecisionLogBase(BaseModel):
    type: str = Field(..., pattern="^(note|reflection|state_change)$")
    content: str = Field(..., min_length=1, max_length=10000)
    source: str = Field(default="human", pattern="^(human|system)$")


class DecisionLogCreate(DecisionLogBase):
    @model_validator(mode="after")
    def validate_source_for_state_change(self):
        if self.type == "state_change" and self.source != "system":
            raise ValueError("state_change logs can only be created by the system")
        if self.type in ("note", "reflection") and self.source == "system":
            raise ValueError("note/reflection logs must have source=human")
        return self


class DecisionLogResponse(DecisionLogBase):
    id: str
    decision_id: str
    created_at: datetime

    class Config:
        from_attributes = True
