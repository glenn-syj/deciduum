from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date
from typing import Optional

from app.core.database import get_db
from app.models.models import Decision, DecisionLog, Direction, Task
from app.schemas.decision import DecisionCreate, DecisionUpdate, DecisionResponse
from app.schemas.decision_log import DecisionLogCreate, DecisionLogResponse
from app.schemas.task import TaskCreate, TaskResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/decisions", tags=["decisions"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response."""
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@router.get("", response_model=PaginatedResponse)
async def list_decisions(
    status: Optional[str] = Query(None, pattern="^(completed|ongoing|archived)$"),
    direction_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(date|created_at|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all decisions with filters and pagination."""
    # Build base query with soft delete filter
    conditions = [Decision.deleted_at.is_(None)]

    if status:
        conditions.append(Decision.status == status)
    if direction_id:
        conditions.append(Decision.direction_id == direction_id)
    if date_from:
        conditions.append(Decision.date >= date_from)
    if date_to:
        conditions.append(Decision.date <= date_to)

    # Count total
    count_query = select(func.count(Decision.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * limit
    sort_column = getattr(Decision, sort_by, Decision.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()

    query = (
        select(Decision)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    decisions = result.scalars().all()

    return PaginatedResponse(
        data=[DecisionResponse.model_validate(d) for d in decisions],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    )


@router.post("", status_code=201, response_model=dict)
async def create_decision(
    decision: DecisionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new decision."""
    # Validate direction_id if provided
    if decision.direction_id:
        dir_query = select(Direction).where(
            and_(Direction.id == decision.direction_id, Direction.deleted_at.is_(None))
        )
        dir_result = await db.execute(dir_query)
        direction = dir_result.scalar_one_or_none()
        if not direction:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    "CONSTRAINT_VIOLATION",
                    "Referenced resource does not exist",
                    {
                        "field": "direction_id",
                        "value": decision.direction_id,
                        "referenced_resource": "direction",
                    },
                ),
            )

    # Validate review_at >= date if both provided
    if decision.review_at and decision.date:
        if decision.review_at < decision.date:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    "INVALID_DATE_RANGE",
                    "Review date must be on or after the decision date",
                    {
                        "field": "review_at",
                        "date": decision.date,
                        "review_at": decision.review_at,
                    },
                ),
            )

    # Convert string dates to date objects
    review_at_date = None
    if decision.review_at:
        review_at_date = datetime.strptime(decision.review_at, "%Y-%m-%d").date()

    db_decision = Decision(
        title=decision.title,
        date=datetime.strptime(decision.date, "%Y-%m-%d").date(),
        status=decision.status,
        review_at=review_at_date,
        direction_id=decision.direction_id,
    )
    db.add(db_decision)
    await db.commit()
    await db.refresh(db_decision)

    return {"data": DecisionResponse.model_validate(db_decision)}


@router.get("/{decision_id}", response_model=dict)
async def get_decision(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single decision by ID."""
    query = select(Decision).where(
        and_(Decision.id == decision_id, Decision.deleted_at.is_(None))
    )
    result = await db.execute(query)
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision not found",
                {"resource_type": "decision", "id": decision_id},
            ),
        )

    return {"data": DecisionResponse.model_validate(decision)}


@router.patch("/{decision_id}", response_model=dict)
async def update_decision(
    decision_id: str,
    decision: DecisionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a decision."""
    query = select(Decision).where(
        and_(Decision.id == decision_id, Decision.deleted_at.is_(None))
    )
    result = await db.execute(query)
    db_decision = result.scalar_one_or_none()

    if not db_decision:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision not found",
                {"resource_type": "decision", "id": decision_id},
            ),
        )

    # Validate direction_id if provided
    if decision.direction_id is not None:
        if decision.direction_id:
            dir_query = select(Direction).where(
                and_(
                    Direction.id == decision.direction_id,
                    Direction.deleted_at.is_(None),
                )
            )
            dir_result = await db.execute(dir_query)
            direction = dir_result.scalar_one_or_none()
            if not direction:
                raise HTTPException(
                    status_code=422,
                    detail=create_error_response(
                        "CONSTRAINT_VIOLATION",
                        "Referenced resource does not exist",
                        {
                            "field": "direction_id",
                            "value": decision.direction_id,
                            "referenced_resource": "direction",
                        },
                    ),
                )
        db_decision.direction_id = decision.direction_id

    # Validate review_at >= date if both provided
    update_date = decision.date or str(db_decision.date)
    update_review_at = (
        decision.review_at
        if decision.review_at is not None
        else (str(db_decision.review_at) if db_decision.review_at else None)
    )

    if update_review_at and update_date:
        if update_review_at < update_date:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    "INVALID_DATE_RANGE",
                    "Review date must be on or after the decision date",
                    {
                        "field": "review_at",
                        "date": update_date,
                        "review_at": update_review_at,
                    },
                ),
            )

    # Update fields
    if decision.title is not None:
        db_decision.title = decision.title
    if decision.date is not None:
        db_decision.date = datetime.strptime(decision.date, "%Y-%m-%d").date()
    if decision.status is not None:
        db_decision.status = decision.status
    if decision.review_at is not None:
        db_decision.review_at = datetime.strptime(decision.review_at, "%Y-%m-%d").date()

    db_decision.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_decision)

    return {"data": DecisionResponse.model_validate(db_decision)}


@router.delete("/{decision_id}", status_code=204)
async def delete_decision(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a decision."""
    query = select(Decision).where(
        and_(Decision.id == decision_id, Decision.deleted_at.is_(None))
    )
    result = await db.execute(query)
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Decision not found",
                {"resource_type": "decision", "id": decision_id},
            ),
        )

    # Soft delete
    decision.deleted_at = datetime.utcnow()
    await db.commit()

    return None


# Decision Logs endpoints


@router.get("/{decision_id}/logs", response_model=PaginatedResponse)
async def list_decision_logs(
    decision_id: str,
    log_type: Optional[str] = Query(None, pattern="^(note|reflection|state_change)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all logs for a decision."""
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

    return PaginatedResponse(
        data=[DecisionLogResponse.model_validate(log) for log in logs],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    )


@router.post("/{decision_id}/logs", status_code=201, response_model=dict)
async def create_decision_log(
    decision_id: str,
    log: DecisionLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new decision log."""
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

    db_log = DecisionLog(
        decision_id=decision_id,
        type=log.type,
        content=log.content,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)

    return {"data": DecisionLogResponse.model_validate(db_log)}


@router.get("/{decision_id}/logs/{log_id}", response_model=dict)
async def get_decision_log(
    decision_id: str,
    log_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single decision log by ID."""
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

    query = select(DecisionLog).where(
        and_(DecisionLog.id == log_id, DecisionLog.decision_id == decision_id)
    )
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

    return {"data": DecisionLogResponse.model_validate(log)}


# Decision Tasks endpoints


@router.get("/{decision_id}/tasks", response_model=PaginatedResponse)
async def list_decision_tasks(
    decision_id: str,
    status: Optional[str] = Query(None, pattern="^(pending|in_progress|completed)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|due_date|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks for a decision."""
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
    conditions = [Task.decision_id == decision_id, Task.deleted_at.is_(None)]
    if status:
        conditions.append(Task.status == status)

    # Count total
    count_query = select(func.count(Task.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * limit
    sort_column = getattr(Task, sort_by, Task.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()

    query = (
        select(Task)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    tasks = result.scalars().all()

    return PaginatedResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    )


@router.post("/{decision_id}/tasks", status_code=201, response_model=dict)
async def create_decision_task(
    decision_id: str,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new task for a decision."""
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

    # If decision_id is provided in body, ensure it matches path
    if task.decision_id and task.decision_id != decision_id:
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                "CONSTRAINT_VIOLATION",
                "Decision ID in body must match path parameter",
                {
                    "field": "decision_id",
                    "path_value": decision_id,
                    "body_value": task.decision_id,
                },
            ),
        )

    db_task = Task(
        title=task.title,
        status=task.status,
        due_date=task.due_date,
        notes=task.notes,
        decision_id=decision_id,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return {"data": TaskResponse.model_validate(db_task)}
