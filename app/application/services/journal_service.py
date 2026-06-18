from datetime import date
from uuid import UUID

from app.domain.entities.journal_entry import JournalEntry
from app.domain.interfaces.journal_repository import JournalRepository
from app.domain.interfaces.user_repository import UserRepository
from app.shared.exceptions import NotFoundError, OwnershipError


class JournalService:
    def __init__(
        self,
        journal_repository: JournalRepository,
        user_repository: UserRepository,
    ) -> None:
        self.journal_repository = journal_repository
        self.user_repository = user_repository

    def create_entry(
        self,
        user_id: UUID,
        raw_text: str,
        entry_date: date | None = None,
    ) -> JournalEntry:
        if not raw_text.strip():
            raise ValueError("Journal entry text must not be empty")

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        return self.journal_repository.create(
            user_id=user.id,
            raw_text=raw_text,
            entry_date=entry_date or date.today(),
        )

    def get_entry_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry:
        entry = self.journal_repository.get_for_user(entry_id=entry_id, user_id=user_id)
        if entry is None:
            raise OwnershipError("Journal entry does not belong to this user")
        return entry

    def list_entries_for_user(self, user_id: UUID) -> list[JournalEntry]:
        return self.journal_repository.list_for_user(user_id)
