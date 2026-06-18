from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.journal_entry import JournalEntry


class JournalRepository(ABC):
    @abstractmethod
    def create(
        self,
        user_id: UUID,
        raw_text: str,
        entry_date: date,
        mood_score: int | None = None,
        mood_label: str | None = None,
        tags: list[str] | None = None,
    ) -> JournalEntry:
        raise NotImplementedError

    @abstractmethod
    def get_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_user(self, user_id: UUID) -> list[JournalEntry]:
        raise NotImplementedError

    @abstractmethod
    def list_for_user_by_date(
        self,
        user_id: UUID,
        entry_date: date,
    ) -> list[JournalEntry]:
        raise NotImplementedError

    @abstractmethod
    def list_for_user_between(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[JournalEntry]:
        raise NotImplementedError

    @abstractmethod
    def search_for_user(self, user_id: UUID, keyword: str) -> list[JournalEntry]:
        raise NotImplementedError

    @abstractmethod
    def delete_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        raise NotImplementedError

    @abstractmethod
    def delete_latest_for_user(self, user_id: UUID) -> JournalEntry | None:
        raise NotImplementedError
