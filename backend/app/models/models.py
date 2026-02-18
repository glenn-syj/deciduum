import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from typing import Optional


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow_string() -> str:
    return datetime.utcnow().isoformat()


class Direction(Base):
    __tablename__ = "directions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(String(36), default=utcnow_string)
    updated_at: Mapped[str] = mapped_column(
        String(36), default=utcnow_string, onupdate=utcnow_string
    )
    deleted_at: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    decisions: Mapped[list["Decision"]] = relationship(
        "Decision", back_populates="direction"
    )
    memos: Mapped[list["Memo"]] = relationship("Memo", back_populates="direction")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(
        String(20), default="ongoing"
    )  # ongoing/completed/archived
    review_at: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    direction_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("directions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String(36), default=utcnow_string)
    updated_at: Mapped[str] = mapped_column(
        String(36), default=utcnow_string, onupdate=utcnow_string
    )
    deleted_at: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    direction: Mapped[Optional["Direction"]] = relationship(
        "Direction", back_populates="decisions"
    )
    logs: Mapped[list["DecisionLog"]] = relationship(
        "DecisionLog", back_populates="decision", cascade="all, delete-orphan"
    )
    memos: Mapped[list["Memo"]] = relationship("Memo", back_populates="linked_decision")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="decision")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    decision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # note/reflection/state_change
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(36), default=utcnow_string)

    decision: Mapped["Decision"] = relationship("Decision", back_populates="logs")


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    linked_decision_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True
    )
    linked_direction_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("directions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String(36), default=utcnow_string)
    updated_at: Mapped[str] = mapped_column(
        String(36), default=utcnow_string, onupdate=utcnow_string
    )
    deleted_at: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    linked_decision: Mapped[Optional["Decision"]] = relationship(
        "Decision", back_populates="memos"
    )
    direction: Mapped[Optional["Direction"]] = relationship(
        "Direction", back_populates="memos"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending/in_progress/completed
    due_date: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # YYYY-MM-DD
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(36), default=utcnow_string)
    updated_at: Mapped[str] = mapped_column(
        String(36), default=utcnow_string, onupdate=utcnow_string
    )
    deleted_at: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    decision: Mapped["Decision"] = relationship("Decision", back_populates="tasks")
