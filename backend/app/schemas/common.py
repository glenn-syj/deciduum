from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: dict


class TodayResponse(BaseModel):
    date: str
    ongoing_decisions: list = []
    todays_decisions: list = []
    todays_memos: list = []
