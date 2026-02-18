from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.models import Task, Decision
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response."""
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@router.get("", response_model=PaginatedResponse)
async def list_tasks(
    decision_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern="^(pending|in_progress|completed)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|due_date|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks with filters and pagination."""
    # Build base query with soft delete filter
    conditions = [Task.deleted_at.is_(None)]

    if decision_id:
        conditions.append(Task.decision_id == decision_id)
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


@router.post("", status_code=201, response_model=dict)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    # Validate decision_id exists
    decision_query = select(Decision).where(
        and_(Decision.id == task.decision_id, Decision.deleted_at.is_(None))
    )
    decision_result = await db.execute(decision_query)
    decision = decision_result.scalar_one_or_none()
    if not decision:
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                "CONSTRAINT_VIOLATION",
                "Referenced resource does not exist",
                {
                    "field": "decision_id",
                    "value": task.decision_id,
                    "referenced_resource": "decision",
                },
            ),
        )

    db_task = Task(
        title=task.title,
        status=task.status,
        due_date=task.due_date,
        notes=task.notes,
        decision_id=task.decision_id,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return {"data": TaskResponse.model_validate(db_task)}


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single task by ID."""
    query = select(Task).where(and_(Task.id == task_id, Task.deleted_at.is_(None)))
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Task not found",
                {"resource_type": "task", "id": task_id},
            ),
        )

    return {"data": TaskResponse.model_validate(task)}


@router.patch("/{task_id}", response_model=dict)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    query = select(Task).where(and_(Task.id == task_id, Task.deleted_at.is_(None)))
    result = await db.execute(query)
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Task not found",
                {"resource_type": "task", "id": task_id},
            ),
        )

    # Validate decision_id if provided
    if task.decision_id is not None:
        if task.decision_id:
            decision_query = select(Decision).where(
                and_(
                    Decision.id == task.decision_id,
                    Decision.deleted_at.is_(None),
                )
            )
            decision_result = await db.execute(decision_query)
            decision = decision_result.scalar_one_or_none()
            if not decision:
                raise HTTPException(
                    status_code=422,
                    detail=create_error_response(
                        "CONSTRAINT_VIOLATION",
                        "Referenced resource does not exist",
                        {
                            "field": "decision_id",
                            "value": task.decision_id,
                            "referenced_resource": "decision",
                        },
                    ),
                )
        db_task.decision_id = task.decision_id

    # Update fields
    if task.title is not None:
        db_task.title = task.title
    if task.status is not None:
        db_task.status = task.status
    if task.due_date is not None:
        db_task.due_date = task.due_date
    if task.notes is not None:
        db_task.notes = task.notes

    db_task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_task)

    return {"data": TaskResponse.model_validate(db_task)}


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a task."""
    query = select(Task).where(and_(Task.id == task_id, Task.deleted_at.is_(None)))
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Task not found",
                {"resource_type": "task", "id": task_id},
            ),
        )

    # Soft delete
    task.deleted_at = datetime.utcnow()
    await db.commit()

    return None
