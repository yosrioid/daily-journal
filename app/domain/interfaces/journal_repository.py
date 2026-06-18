from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.journal_entry import JournalEntry


class JournalRepository(ABC):
    @abstractmethod
    def create(self, user_id: UUID, raw_text: str, entry_date: date) -> JournalEntry:
        raise NotImplementedError

    @abstractmethod
    def get_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_user(self, user_id: UUID) -> list[JournalEntry]:
        raise NotImplementedError
