from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import Optional

from app.core.database import get_db_from_header, DEFAULT_SESSION_ID
from app.models.models import Memo, Decision, Direction
from app.schemas.memo import MemoCreate, MemoUpdate, MemoResponse

router = APIRouter(prefix="/memos", tags=["memos"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response."""
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@router.get("", response_model=dict)
async def list_memos(
    date_from: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    linked_decision_id: Optional[str] = Query(None),
    linked_direction_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(date|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_from_header),
):
    """List all memos with filters and pagination."""
    # Build base query with soft delete filter
    conditions = [Memo.deleted_at.is_(None)]

    if date_from:
        conditions.append(Memo.date >= date_from)
    if date_to:
        conditions.append(Memo.date <= date_to)
    if linked_decision_id:
        conditions.append(Memo.linked_decision_id == linked_decision_id)
    if linked_direction_id:
        conditions.append(Memo.linked_direction_id == linked_direction_id)

    # Count total
    count_query = select(func.count(Memo.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * limit
    sort_column = getattr(Memo, sort_by, Memo.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()

    query = (
        select(Memo)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    memos = result.scalars().all()

    return {
        "memos": [MemoResponse.model_validate(m) for m in memos],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    }


@router.post("", status_code=201, response_model=dict)
async def create_memo(
    memo: MemoCreate,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Create a new memo."""
    # Validate linked_decision_id if provided
    if memo.linked_decision_id:
        decision_query = select(Decision).where(
            and_(Decision.id == memo.linked_decision_id, Decision.deleted_at.is_(None))
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
                        "field": "linked_decision_id",
                        "value": memo.linked_decision_id,
                        "referenced_resource": "decision",
                    },
                ),
            )

    # Validate linked_direction_id if provided
    if memo.linked_direction_id:
        direction_query = select(Direction).where(
            and_(
                Direction.id == memo.linked_direction_id, Direction.deleted_at.is_(None)
            )
        )
        direction_result = await db.execute(direction_query)
        direction = direction_result.scalar_one_or_none()
        if not direction:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    "CONSTRAINT_VIOLATION",
                    "Referenced resource does not exist",
                    {
                        "field": "linked_direction_id",
                        "value": memo.linked_direction_id,
                        "referenced_resource": "direction",
                    },
                ),
            )

    db_memo = Memo(
        content=memo.content,
        date=memo.date,
        linked_decision_id=memo.linked_decision_id,
        linked_direction_id=memo.linked_direction_id,
    )
    db.add(db_memo)
    await db.commit()
    await db.refresh(db_memo)

    return {"data": MemoResponse.model_validate(db_memo)}


@router.get("/{memo_id}", response_model=dict)
async def get_memo(
    memo_id: str,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Get a single memo by ID."""
    query = select(Memo).where(and_(Memo.id == memo_id, Memo.deleted_at.is_(None)))
    result = await db.execute(query)
    memo = result.scalar_one_or_none()

    if not memo:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Memo not found",
                {"resource_type": "memo", "id": memo_id},
            ),
        )

    return {"data": MemoResponse.model_validate(memo)}


@router.patch("/{memo_id}", response_model=dict)
async def update_memo(
    memo_id: str,
    memo: MemoUpdate,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Update a memo."""
    query = select(Memo).where(and_(Memo.id == memo_id, Memo.deleted_at.is_(None)))
    result = await db.execute(query)
    db_memo = result.scalar_one_or_none()

    if not db_memo:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Memo not found",
                {"resource_type": "memo", "id": memo_id},
            ),
        )

    # Validate linked_decision_id if provided
    if memo.linked_decision_id is not None:
        if memo.linked_decision_id:
            decision_query = select(Decision).where(
                and_(
                    Decision.id == memo.linked_decision_id,
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
                            "field": "linked_decision_id",
                            "value": memo.linked_decision_id,
                            "referenced_resource": "decision",
                        },
                    ),
                )
        db_memo.linked_decision_id = memo.linked_decision_id

    # Validate linked_direction_id if provided
    if memo.linked_direction_id is not None:
        if memo.linked_direction_id:
            direction_query = select(Direction).where(
                and_(
                    Direction.id == memo.linked_direction_id,
                    Direction.deleted_at.is_(None),
                )
            )
            direction_result = await db.execute(direction_query)
            direction = direction_result.scalar_one_or_none()
            if not direction:
                raise HTTPException(
                    status_code=422,
                    detail=create_error_response(
                        "CONSTRAINT_VIOLATION",
                        "Referenced resource does not exist",
                        {
                            "field": "linked_direction_id",
                            "value": memo.linked_direction_id,
                            "referenced_resource": "direction",
                        },
                    ),
                )
        db_memo.linked_direction_id = memo.linked_direction_id

    # Update fields
    if memo.content is not None:
        db_memo.content = memo.content
    if memo.date is not None:
        db_memo.date = memo.date

    db_memo.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_memo)

    return {"data": MemoResponse.model_validate(db_memo)}


@router.delete("/{memo_id}", status_code=204)
async def delete_memo(
    memo_id: str,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Soft delete a memo."""
    query = select(Memo).where(and_(Memo.id == memo_id, Memo.deleted_at.is_(None)))
    result = await db.execute(query)
    memo = result.scalar_one_or_none()

    if not memo:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Memo not found",
                {"resource_type": "memo", "id": memo_id},
            ),
        )

    # Soft delete
    memo.deleted_at = datetime.utcnow()
    await db.commit()

    return None
