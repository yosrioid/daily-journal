from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import JournalEntryModel, UserModel
from app.infrastructure.database.session import get_session
from app.main import create_app
from app.shared.config import Settings


def build_client(db_session: Session) -> TestClient:
    app = create_app(Settings(TELEGRAM_WEBHOOK_SECRET="test-secret"))

    def override_get_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def telegram_update(text: str, unix_timestamp: int = 1781730000) -> dict[str, object]:
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": unix_timestamp,
            "text": text,
            "from": {
                "id": 123456,
                "is_bot": False,
                "username": "journaler",
                "first_name": "Journal",
                "last_name": "User",
            },
        },
    }


def test_telegram_webhook_rejects_invalid_secret(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("Today was productive."),
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )

    assert response.status_code == 403


def test_telegram_webhook_saves_text_message(db_session: Session) -> None:
    client = build_client(db_session)
    unix_timestamp = int(datetime(2026, 6, 17, 18, 0, tzinfo=UTC).timestamp())

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("Today was productive.", unix_timestamp),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "journal_saved"
    assert response.json()["reply_text"] == "Journal saved."

    user = db_session.scalar(
        select(UserModel).where(UserModel.telegram_user_id == 123456),
    )
    assert user is not None
    entry = db_session.scalar(select(JournalEntryModel))
    assert entry is not None
    assert entry.user_id == user.id
    assert entry.raw_text == "Today was productive."
    assert entry.entry_date.isoformat() == "2026-06-18"


def test_telegram_start_registers_user_without_journal(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/start"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_start"
    assert "Daily Journal is active." in response.json()["reply_text"]
    assert db_session.scalar(select(UserModel)) is not None
    assert db_session.scalar(select(JournalEntryModel)) is None


def test_telegram_webhook_ignores_update_without_message(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json={"update_id": 2},
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "action": "ignored",
        "reply_text": None,
        "journal_entry_id": None,
    }
