from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class Report:
    id: UUID
    user_id: UUID
    report_type: str
    period_start: date
    period_end: date
    mood_average: float | None
    mood_min: int | None
    mood_max: int | None
    summary: str | None
    dominant_topics: list[str] | None
    positive_patterns: list[str] | None
    negative_patterns: list[str] | None
    key_events: list[str] | None
    lessons_learned: list[str] | None
    recommendations: list[str] | None
    created_at: datetime
    updated_at: datetime
