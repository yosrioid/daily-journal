from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class JournalEntry:
    id: UUID
    user_id: UUID
    entry_date: date
    raw_text: str
    processed_text: str | None
    summary: str | None
    mood_score: int | None
    mood_label: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime
