from sqlalchemy.orm import Session

from app.application.services.user_service import UserService
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository


def test_create_new_user_from_telegram_message(db_session: Session) -> None:
    service = UserService(SQLAlchemyUserRepository(db_session))

    user = service.resolve_telegram_user(
        telegram_user_id=98765,
        telegram_username="journaler",
        first_name="Journal",
        last_name="User",
    )

    assert user.telegram_user_id == 98765
    assert user.telegram_username == "journaler"
    assert user.first_name == "Journal"
    assert user.last_name == "User"
    assert user.timezone == "Asia/Jakarta"


def test_existing_user_profile_is_updated_from_telegram(db_session: Session) -> None:
    service = UserService(SQLAlchemyUserRepository(db_session))
    original = service.resolve_telegram_user(
        telegram_user_id=777,
        telegram_username="oldname",
        first_name="Old",
    )

    updated = service.resolve_telegram_user(
        telegram_user_id=777,
        telegram_username="newname",
        first_name="New",
        last_name="Name",
    )

    assert updated.id == original.id
    assert updated.telegram_username == "newname"
    assert updated.first_name == "New"
    assert updated.last_name == "Name"


def test_user_timezone_can_be_updated(db_session: Session) -> None:
    service = UserService(SQLAlchemyUserRepository(db_session))
    user = service.resolve_telegram_user(telegram_user_id=778)

    updated = service.update_timezone(user, "America/Los_Angeles")

    assert updated.id == user.id
    assert updated.timezone == "America/Los_Angeles"
