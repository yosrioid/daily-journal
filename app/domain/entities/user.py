from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    telegram_user_id: int
    telegram_username: str | None
    first_name: str | None
    last_name: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime
