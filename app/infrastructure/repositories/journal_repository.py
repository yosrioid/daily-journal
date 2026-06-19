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

    def create(
        self,
        user_id: UUID,
        raw_text: str,
        entry_date: date,
        mood_score: int | None = None,
        mood_label: str | None = None,
        tags: list[str] | None = None,
    ) -> JournalEntry:
        model = JournalEntryModel(
            user_id=user_id,
            raw_text=raw_text,
            entry_date=entry_date,
            mood_score=mood_score,
            mood_label=mood_label,
            tags=tags,
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
            .order_by(*self._default_ordering())
        )
        return [self._to_entity(model) for model in self.session.scalars(statement)]

    def list_for_user_by_date(
        self,
        user_id: UUID,
        entry_date: date,
    ) -> list[JournalEntry]:
        statement = (
            select(JournalEntryModel)
            .where(
                JournalEntryModel.user_id == user_id,
                JournalEntryModel.entry_date == entry_date,
            )
            .order_by(JournalEntryModel.created_at.desc())
        )
        return [self._to_entity(model) for model in self.session.scalars(statement)]

    def list_for_user_between(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[JournalEntry]:
        statement = (
            select(JournalEntryModel)
            .where(
                JournalEntryModel.user_id == user_id,
                JournalEntryModel.entry_date >= start_date,
                JournalEntryModel.entry_date <= end_date,
            )
            .order_by(JournalEntryModel.entry_date, JournalEntryModel.created_at)
        )
        return [self._to_entity(model) for model in self.session.scalars(statement)]

    def search_for_user(self, user_id: UUID, keyword: str) -> list[JournalEntry]:
        statement = (
            select(JournalEntryModel)
            .where(
                JournalEntryModel.user_id == user_id,
                JournalEntryModel.raw_text.ilike(f"%{keyword}%"),
            )
            .order_by(*self._default_ordering())
        )
        return [self._to_entity(model) for model in self.session.scalars(statement)]

    def update_for_user(
        self,
        entry_id: UUID,
        user_id: UUID,
        entry_date: date | None = None,
        processed_text: str | None = None,
        summary: str | None = None,
        mood_score: int | None = None,
        mood_label: str | None = None,
        tags: list[str] | None = None,
    ) -> JournalEntry | None:
        model = self._get_model_for_user(entry_id=entry_id, user_id=user_id)
        if model is None:
            return None

        if entry_date is not None:
            model.entry_date = entry_date
        if processed_text is not None:
            model.processed_text = processed_text
        if summary is not None:
            model.summary = summary
        if mood_score is not None:
            model.mood_score = mood_score
        if mood_label is not None:
            model.mood_label = mood_label
        if tags is not None:
            model.tags = tags
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def delete_for_user(self, entry_id: UUID, user_id: UUID) -> JournalEntry | None:
        model = self._get_model_for_user(entry_id=entry_id, user_id=user_id)
        if model is None:
            return None

        entry = self._to_entity(model)
        self.session.delete(model)
        self.session.flush()
        return entry

    def delete_latest_for_user(self, user_id: UUID) -> JournalEntry | None:
        statement = (
            select(JournalEntryModel)
            .where(JournalEntryModel.user_id == user_id)
            .order_by(*self._default_ordering())
            .limit(1)
        )
        model = self.session.scalar(statement)
        if model is None:
            return None

        entry = self._to_entity(model)
        self.session.delete(model)
        self.session.flush()
        return entry

    def _get_model_for_user(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> JournalEntryModel | None:
        statement = select(JournalEntryModel).where(
            JournalEntryModel.id == entry_id,
            JournalEntryModel.user_id == user_id,
        )
        return self.session.scalar(statement)

    def _default_ordering(self) -> tuple[object, object]:
        return (
            JournalEntryModel.entry_date.desc(),
            JournalEntryModel.created_at.desc(),
        )

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
