from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from datetime import datetime
from typing import Optional

from app.core.database import get_db_from_header, DEFAULT_SESSION_ID
from app.models.models import Direction, Decision, Memo
from app.schemas.direction import (
    DirectionCreate,
    DirectionUpdate,
    DirectionResponse,
    DirectionWithDetails,
)
from app.schemas.decision import DecisionResponse
from app.schemas.memo import MemoResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/directions", tags=["directions"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response."""
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


@router.get("", response_model=PaginatedResponse)
async def list_directions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_from_header),
):
    """List all directions with pagination."""
    # Build base query with soft delete filter
    conditions = [Direction.deleted_at.is_(None)]

    # Count total
    count_query = select(func.count(Direction.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * limit
    sort_column = getattr(Direction, sort_by, Direction.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()

    query = (
        select(Direction)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    directions = result.scalars().all()

    return PaginatedResponse(
        data=[DirectionResponse.model_validate(d) for d in directions],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    )


@router.post("", status_code=201, response_model=dict)
async def create_direction(
    direction: DirectionCreate,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Create a new direction."""
    # Check for duplicate title
    query = select(Direction).where(
        and_(Direction.title == direction.title, Direction.deleted_at.is_(None))
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=create_error_response(
                "DUPLICATE_RESOURCE",
                "A direction with this title already exists",
                {
                    "resource_type": "direction",
                    "field": "title",
                    "value": direction.title,
                },
            ),
        )

    db_direction = Direction(title=direction.title)
    db.add(db_direction)
    await db.commit()
    await db.refresh(db_direction)

    return {"data": DirectionResponse.model_validate(db_direction)}


@router.get("/{direction_id}", response_model=dict)
async def get_direction(
    direction_id: str,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Get a single direction by ID."""
    query = select(Direction).where(
        and_(Direction.id == direction_id, Direction.deleted_at.is_(None))
    )
    result = await db.execute(query)
    direction = result.scalar_one_or_none()

    if not direction:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Direction not found",
                {"resource_type": "direction", "id": direction_id},
            ),
        )

    return {"data": DirectionResponse.model_validate(direction)}


@router.patch("/{direction_id}", response_model=dict)
async def update_direction(
    direction_id: str,
    direction: DirectionUpdate,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Update a direction."""
    query = select(Direction).where(
        and_(Direction.id == direction_id, Direction.deleted_at.is_(None))
    )
    result = await db.execute(query)
    db_direction = result.scalar_one_or_none()

    if not db_direction:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Direction not found",
                {"resource_type": "direction", "id": direction_id},
            ),
        )

    # Check for duplicate title if title is being updated
    if direction.title is not None and direction.title != db_direction.title:
        check_query = select(Direction).where(
            and_(
                Direction.title == direction.title,
                Direction.deleted_at.is_(None),
                Direction.id != direction_id,
            )
        )
        check_result = await db.execute(check_query)
        existing = check_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=create_error_response(
                    "DUPLICATE_RESOURCE",
                    "A direction with this title already exists",
                    {
                        "resource_type": "direction",
                        "field": "title",
                        "value": direction.title,
                    },
                ),
            )
        db_direction.title = direction.title

    db_direction.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_direction)

    return {"data": DirectionResponse.model_validate(db_direction)}


@router.delete("/{direction_id}", status_code=204)
async def delete_direction(
    direction_id: str,
    db: AsyncSession = Depends(get_db_from_header),
):
    """Soft delete a direction."""
    query = select(Direction).where(
        and_(Direction.id == direction_id, Direction.deleted_at.is_(None))
    )
    result = await db.execute(query)
    direction = result.scalar_one_or_none()

    if not direction:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Direction not found",
                {"resource_type": "direction", "id": direction_id},
            ),
        )

    # Soft delete - direction_id in decisions and memos will be set to null via FK cascade
    direction.deleted_at = datetime.utcnow()

    # Clear direction_id from linked decisions (SQLite's ON DELETE SET NULL doesn't work for soft deletes)
    await db.execute(
        update(Decision)
        .where(Decision.direction_id == direction_id)
        .values(direction_id=None)
    )

    # Clear linked_direction_id from linked memos
    await db.execute(
        update(Memo)
        .where(Memo.linked_direction_id == direction_id)
        .values(linked_direction_id=None)
    )

    await db.commit()

    return None


@router.get("/{direction_id}/details", response_model=dict)
async def get_direction_with_details(
    direction_id: str,
    decision_status: Optional[str] = Query(
        None, pattern="^(completed|ongoing|archived)$"
    ),
    decision_page: int = Query(1, ge=1),
    decision_limit: int = Query(20, ge=1, le=100),
    memo_page: int = Query(1, ge=1),
    memo_limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_from_header),
):
    """Get a direction with all associated decisions and memos."""
    # Get direction
    direction_query = select(Direction).where(
        and_(Direction.id == direction_id, Direction.deleted_at.is_(None))
    )
    direction_result = await db.execute(direction_query)
    direction = direction_result.scalar_one_or_none()

    if not direction:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                "RESOURCE_NOT_FOUND",
                "Direction not found",
                {"resource_type": "direction", "id": direction_id},
            ),
        )

    # Build decisions query
    decision_conditions = [
        Decision.direction_id == direction_id,
        Decision.deleted_at.is_(None),
    ]
    if decision_status:
        decision_conditions.append(Decision.status == decision_status)

    # Count decisions
    decision_count_query = select(func.count(Decision.id)).where(
        and_(*decision_conditions)
    )
    decision_count_result = await db.execute(decision_count_query)
    decisions_total = decision_count_result.scalar() or 0

    # Get decisions
    decision_offset = (decision_page - 1) * decision_limit
    decisions_query = (
        select(Decision)
        .where(and_(*decision_conditions))
        .order_by(Decision.date.desc())
        .offset(decision_offset)
        .limit(decision_limit)
    )
    decisions_result = await db.execute(decisions_query)
    decisions = decisions_result.scalars().all()

    # Build memos query
    memo_conditions = [
        Memo.linked_direction_id == direction_id,
        Memo.deleted_at.is_(None),
    ]

    # Count memos
    memo_count_query = select(func.count(Memo.id)).where(and_(*memo_conditions))
    memo_count_result = await db.execute(memo_count_query)
    memos_total = memo_count_result.scalar() or 0

    # Get memos
    memo_offset = (memo_page - 1) * memo_limit
    memos_query = (
        select(Memo)
        .where(and_(*memo_conditions))
        .order_by(Memo.date.desc())
        .offset(memo_offset)
        .limit(memo_limit)
    )
    memos_result = await db.execute(memos_query)
    memos = memos_result.scalars().all()

    # Build response
    direction_data = DirectionResponse.model_validate(direction)

    return {
        "data": {
            "id": direction_data.id,
            "title": direction_data.title,
            "created_at": direction_data.created_at,
            "updated_at": direction_data.updated_at,
            "decisions": {
                "data": [DecisionResponse.model_validate(d) for d in decisions],
                "meta": {
                    "page": decision_page,
                    "limit": decision_limit,
                    "total": decisions_total,
                    "total_pages": (decisions_total + decision_limit - 1)
                    // decision_limit
                    if decisions_total > 0
                    else 0,
                },
            },
            "memos": {
                "data": [MemoResponse.model_validate(m) for m in memos],
                "meta": {
                    "page": memo_page,
                    "limit": memo_limit,
                    "total": memos_total,
                    "total_pages": (memos_total + memo_limit - 1) // memo_limit
                    if memos_total > 0
                    else 0,
                },
            },
        }
    }
