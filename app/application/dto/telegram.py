from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TelegramUserPayload:
    telegram_user_id: int
    telegram_username: str | None
    first_name: str | None
    last_name: str | None


@dataclass(frozen=True)
class TelegramMessagePayload:
    message_id: int
    unix_timestamp: int
    text: str | None
    chat_id: int | None
    user: TelegramUserPayload


@dataclass(frozen=True)
class TelegramWebhookResult:
    ok: bool
    action: str
    reply_text: str | None
    user_id: UUID | None = None
    journal_entry_id: UUID | None = None
