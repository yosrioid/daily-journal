from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.journal_entry import JournalEntry
from app.domain.interfaces.journal_repository import JournalRepository
from app.infrastructure.database.models import JournalEntryModel, json_list


class SQLAlchemyJournalRepository(JournalRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_id: UUID, raw_text: str, entry_date: date) -> JournalEntry:
        model = JournalEntryModel(
            user_id=user_id,
            raw_text=raw_text,
            entry_date=entry_date,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def get_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        statement = select(JournalEntryModel).where(
            JournalEntryModel.id == entry_id,
            JournalEntryModel.user_id == user_id,
        )
        model = self.session.scalar(statement)
        return self._to_entity(model) if model is not None else None

    def list_for_user(self, user_id: UUID) -> list[JournalEntry]:
        statement = (
            select(JournalEntryModel)
            .where(JournalEntryModel.user_id == user_id)
            .order_by(
                JournalEntryModel.entry_date.desc(),
                JournalEntryModel.created_at.desc(),
            )
        )
        return [self._to_entity(model) for model in self.session.scalars(statement)]

    def _to_entity(self, model: JournalEntryModel) -> JournalEntry:
        return JournalEntry(
            id=model.id,
            user_id=model.user_id,
            entry_date=model.entry_date,
            raw_text=model.raw_text,
            processed_text=model.processed_text,
            summary=model.summary,
            mood_score=model.mood_score,
            mood_label=model.mood_label,
            tags=json_list(model.tags),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
