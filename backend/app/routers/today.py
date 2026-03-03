from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date as date_obj, datetime
from typing import Optional

from app.core.database import get_db_from_header, DEFAULT_SESSION_ID
from app.models.models import Decision, Memo
from app.schemas.decision import DecisionResponse
from app.schemas.memo import MemoResponse
from app.schemas.common import TodayResponse

router = APIRouter(prefix="/today", tags=["today"])


@router.get("", response_model=dict)
async def get_today_view(
    date: str = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db_from_header),
):
    """Get today's view with ongoing decisions, today's decisions, and today's memos."""
    # Use provided date or default to today
    target_date = date or str(date_obj.today())

    # Query ongoing decisions (not completed, not archived, not deleted)
    ongoing_query = (
        select(Decision)
        .where(
            and_(
                Decision.status == "ongoing",
                Decision.deleted_at.is_(None),
            )
        )
        .order_by(Decision.created_at.desc())
    )
    ongoing_result = await db.execute(ongoing_query)
    ongoing_decisions = ongoing_result.scalars().all()

    # Query decisions made on target date
    todays_decisions_query = (
        select(Decision)
        .where(
            and_(
                Decision.date == target_date,
                Decision.deleted_at.is_(None),
            )
        )
        .order_by(Decision.created_at.desc())
    )
    todays_decisions_result = await db.execute(todays_decisions_query)
    todays_decisions = todays_decisions_result.scalars().all()

    # Query memos on target date
    todays_memos_query = (
        select(Memo)
        .where(
            and_(
                Memo.date == target_date,
                Memo.deleted_at.is_(None),
            )
        )
        .order_by(Memo.created_at.desc())
    )
    todays_memos_result = await db.execute(todays_memos_query)
    todays_memos = todays_memos_result.scalars().all()

    return {
        "data": {
            "date": target_date,
            "ongoing_decisions": [
                DecisionResponse.model_validate(d) for d in ongoing_decisions
            ],
            "todays_decisions": [
                DecisionResponse.model_validate(d) for d in todays_decisions
            ],
            "todays_memos": [MemoResponse.model_validate(m) for m in todays_memos],
        }
    }
