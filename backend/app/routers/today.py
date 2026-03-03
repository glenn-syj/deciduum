from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import date as date_obj, datetime
from typing import Optional

from app.core.database import get_db_from_header, DEFAULT_SESSION_ID
from app.models.models import Decision, Memo, DecisionLog, Task
from app.schemas.decision import DecisionResponse
from app.schemas.memo import MemoResponse
from app.schemas.task import TaskResponse
from app.schemas.decision_log import DecisionLogResponse

router = APIRouter(prefix="/today", tags=["today"])


@router.get("", response_model=dict)
async def get_today_view(
    date: str = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db_from_header),
):
    """Get today's view with ongoing decisions, today's decisions, memos, recent logs, and pending tasks."""
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
    today_decisions = todays_decisions_result.scalars().all()

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
    memos = todays_memos_result.scalars().all()

    # Query recent (latest 10 logs from ongoing decisions)
    ongoing_ids = [d.id for d in ongoing_decisions]
    recent_logs = []
    if ongoing_ids:
        logs_query = (
            select(DecisionLog)
            .where(DecisionLog.decision_id.in_(ongoing_ids))
            .order_by(DecisionLog.created_at.desc())
            .limit(10)
        )
        logs_result = await db.execute(logs_query)
        logs = logs_result.scalars().all()

        # Create a lookup for decision titles
        decision_titles = {d.id: d.title for d in ongoing_decisions}

        for log in logs:
            log_response = DecisionLogResponse.model_validate(log)
            recent_logs.append(
                {
                    "id": log_response.id,
                    "decision_id": log_response.decision_id,
                    "decision_title": decision_titles.get(log_response.decision_id, ""),
                    "type": log_response.type,
                    "content": log_response.content,
                    "source": log_response.source,
                    "created_at": log_response.created_at.isoformat()
                    if log_response.created_at
                    else None,
                }
            )

    # Query pending tasks
    tasks_query = (
        select(Task)
        .options(selectinload(Task.decision))
        .where(
            and_(
                Task.status == "pending",
                Task.deleted_at.is_(None),
            )
        )
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.asc())
    )
    tasks_result = await db.execute(tasks_query)
    pending_tasks = tasks_result.scalars().all()

    # Format pending tasks with decision titles
    formatted_pending_tasks = []
    for task in pending_tasks:
        task_response = TaskResponse.model_validate(task)
        formatted_pending_tasks.append(
            {
                "id": task_response.id,
                "title": task_response.title,
                "status": task_response.status,
                "due_date": task_response.due_date,
                "decision_title": task.decision.title if task.decision else "",
                "decision_id": task_response.decision_id,
                "notes": task_response.notes,
                "created_at": task_response.created_at.isoformat()
                if task_response.created_at
                else None,
                "updated_at": task_response.updated_at.isoformat()
                if task_response.updated_at
                else None,
            }
        )

    return {
        "date": target_date,
        "ongoing_decisions": [
            DecisionResponse.model_validate(d) for d in ongoing_decisions
        ],
        "today_decisions": [
            DecisionResponse.model_validate(d) for d in today_decisions
        ],
        "memos": [MemoResponse.model_validate(m) for m in memos],
        "recent_logs": recent_logs,
        "pending_tasks": formatted_pending_tasks,
    }
