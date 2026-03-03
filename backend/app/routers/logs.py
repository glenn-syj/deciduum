from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import Optional

from app.core.database import get_db_from_header
from app.models.models import Decision, DecisionLog
from app.schemas.decision_log import DecisionLogCreate, DecisionLogResponse

router = APIRouter(prefix="/logs", tags=["logs"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response."""
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@router.post("", status_code=201, response_model=dict)
async def create_log(
    log: DecisionLogCreate,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Create a new log entry."""
    # Validate decision_id exists
    decision_id = log.decision_id
    decision_query = select(Decision).where(
        and_(Decision.id == decision_id, Decision.deleted_at.is_(None))
    )
    decision_result = await db.execute(decision_query)
    decision = decision_result.scalar_one_or_none()

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision not found",
                {"resource_type": "decision", "id": decision_id},
            ),
        )

    db_log = DecisionLog(
        decision_id=decision_id,
        type=log.type,
        content=log.content,
        source=log.source,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)

    return {"data": DecisionLogResponse.model_validate(db_log)}


@router.get("")
async def list_logs(
    decision_id: str = Query(..., description="Filter by decision ID"),
    log_type: Optional[str] = Query(None, pattern="^(note|reflection|state_change)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_from_header),
):
    """List logs for a decision with pagination and filters."""
    # Verify decision exists
    decision_query = select(Decision).where(
        and_(Decision.id == decision_id, Decision.deleted_at.is_(None))
    )
    decision_result = await db.execute(decision_query)
    decision = decision_result.scalar_one_or_none()

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision not found",
                {"resource_type": "decision", "id": decision_id},
            ),
        )

    # Build query
    conditions = [DecisionLog.decision_id == decision_id]
    if log_type:
        conditions.append(DecisionLog.type == log_type)

    # Count total
    count_query = select(func.count(DecisionLog.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * limit
    sort_column = getattr(DecisionLog, sort_by, DecisionLog.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()

    query = (
        select(DecisionLog)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [DecisionLogResponse.model_validate(log) for log in logs],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    }


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: str,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Delete a log entry (hard delete)."""
    query = select(DecisionLog).where(DecisionLog.id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision log not found",
                {"resource_type": "decision_log", "id": log_id},
            ),
        )

    # Hard delete
    await db.delete(log)
    await db.commit()

    return None
