from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    telegram_username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Jakarta",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    journal_entries: Mapped[list["JournalEntryModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class JournalEntryModel(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        Index(
            "ix_journal_entries_user_entry_date_created_at",
            "user_id",
            "entry_date",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    processed_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    mood_score: Mapped[int | None] = mapped_column(Integer)
    mood_label: Mapped[str | None] = mapped_column(String(64))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[UserModel] = relationship(back_populates="journal_entries")


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "report_type",
            "period_start",
            "period_end",
            name="uq_reports_user_type_period",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mood_average: Mapped[float | None] = mapped_column(Float)
    mood_min: Mapped[int | None] = mapped_column(Integer)
    mood_max: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)
    dominant_topics: Mapped[list[str] | None] = mapped_column(JSON)
    positive_patterns: Mapped[list[str] | None] = mapped_column(JSON)
    negative_patterns: Mapped[list[str] | None] = mapped_column(JSON)
    key_events: Mapped[list[str] | None] = mapped_column(JSON)
    lessons_learned: Mapped[list[str] | None] = mapped_column(JSON)
    recommendations: Mapped[list[str] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[UserModel] = relationship(back_populates="reports")


def json_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value]
    return None
