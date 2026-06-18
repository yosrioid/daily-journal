from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.application.services.journal_service import JournalService
from app.application.services.user_service import UserService
from app.infrastructure.repositories.journal_repository import (
    SQLAlchemyJournalRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.shared.exceptions import OwnershipError


def build_services(db_session: Session) -> tuple[UserService, JournalService]:
    user_repository = SQLAlchemyUserRepository(db_session)
    journal_repository = SQLAlchemyJournalRepository(db_session)
    return (
        UserService(user_repository),
        JournalService(journal_repository, user_repository),
    )


def test_existing_user_sends_journal_entry(db_session: Session) -> None:
    user_service, journal_service = build_services(db_session)
    user = user_service.resolve_telegram_user(
        telegram_user_id=12345,
        telegram_username="dailyuser",
        first_name="Daily",
        last_name="User",
    )

    entry = journal_service.create_entry(
        user_id=user.id,
        raw_text="  Today I learned SQLAlchemy basics.  ",
        entry_date=date(2026, 6, 18),
    )

    assert entry.user_id == user.id
    assert entry.entry_date == date(2026, 6, 18)
    assert entry.raw_text == "  Today I learned SQLAlchemy basics.  "


def test_journal_entries_are_isolated_by_user(db_session: Session) -> None:
    user_service, journal_service = build_services(db_session)
    first_user = user_service.resolve_telegram_user(telegram_user_id=1001)
    second_user = user_service.resolve_telegram_user(telegram_user_id=1002)
    first_entry = journal_service.create_entry(
        user_id=first_user.id,
        raw_text="First user's private journal",
        entry_date=date(2026, 6, 18),
    )
    journal_service.create_entry(
        user_id=second_user.id,
        raw_text="Second user's private journal",
        entry_date=date(2026, 6, 18),
    )

    first_user_entries = journal_service.list_entries_for_user(first_user.id)

    assert len(first_user_entries) == 1
    assert first_user_entries[0].id == first_entry.id
    with pytest.raises(OwnershipError):
        journal_service.get_entry_for_user(first_entry.id, second_user.id)
