from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import JournalEntryModel, ReportModel, UserModel
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


def telegram_update_for_user(
    text: str,
    telegram_user_id: int,
    username: str,
    unix_timestamp: int = 1781730000,
) -> dict[str, object]:
    update = telegram_update(text, unix_timestamp)
    message = update["message"]
    assert isinstance(message, dict)
    from_user = message["from"]
    assert isinstance(from_user, dict)
    from_user["id"] = telegram_user_id
    from_user["username"] = username
    return update


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


def test_telegram_webhook_stores_mood_and_tags(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("I made progress learning Python #Backend."),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    entry = db_session.scalar(select(JournalEntryModel))
    assert entry is not None
    assert entry.mood_score is not None
    assert entry.mood_score > 5
    assert entry.mood_label == "positive"
    assert entry.tags == ["backend", "learning"]


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


def test_telegram_today_returns_current_user_entries(db_session: Session) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update("Today entry about Python."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("Another user entry.", 999, "other"),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/today"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_today"
    assert "Today's journal entries" in response.json()["reply_text"]
    assert "Today entry about Python." in response.json()["reply_text"]
    assert "Another user entry." not in response.json()["reply_text"]


def test_telegram_delete_last_deletes_current_user_latest_entry(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update("First entry."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update("Second entry."),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/delete_last"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_delete_last"
    assert "Deleted latest journal entry:" in response.json()["reply_text"]
    entries = db_session.scalars(select(JournalEntryModel)).all()
    assert len(entries) == 1
    assert entries[0].raw_text == "First entry."


def test_telegram_delete_last_handles_empty_journal(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/delete_last"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_delete_last_empty"
    assert response.json()["reply_text"] == "No journal entries to delete."


def test_telegram_delete_last_does_not_delete_another_users_entry(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("Private entry.", 111, "first"),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("/delete_last", 222, "second"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_delete_last_empty"
    entry = db_session.scalar(select(JournalEntryModel))
    assert entry is not None
    assert entry.raw_text == "Private entry."


def test_telegram_weekly_generates_report_without_saving_command(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    client.post(
        "/telegram/webhook",
        json=telegram_update("Progress learning Python #Backend."),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/weekly"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_weekly"
    assert "Weekly Report" in response.json()["reply_text"]
    entry_count = db_session.scalar(select(func.count()).select_from(JournalEntryModel))
    assert entry_count == 1
    report = db_session.scalar(select(ReportModel))
    assert report is not None
    assert report.report_type == "weekly"


def test_telegram_monthly_generates_report_without_saving_command(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    client.post(
        "/telegram/webhook",
        json=telegram_update("Progress learning Python #Backend."),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/monthly"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_monthly"
    assert "Monthly Report" in response.json()["reply_text"]
    entry_count = db_session.scalar(select(func.count()).select_from(JournalEntryModel))
    assert entry_count == 1
    report = db_session.scalar(select(ReportModel))
    assert report is not None
    assert report.report_type == "monthly"


def test_telegram_mood_returns_current_user_summary(db_session: Session) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update("Progress learning Python #Backend."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update("I feel capek and stress."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update("Produktif work session."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("Other user happy progress.", 999, "other"),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/mood"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_mood"
    assert response.json()["reply_text"] == (
        "Mood Summary\n"
        "Entries with mood: 3\n"
        "Average mood: 5.0/10\n"
        "Lowest mood: 1/10\n"
        "Highest mood: 7/10\n"
        "Most common mood: positive"
    )


def test_telegram_mood_handles_empty_data(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/mood"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_mood"
    assert response.json()["reply_text"] == "No mood data available yet."


def test_telegram_search_returns_matching_user_entries(db_session: Session) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update("Learning Python backend today."),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update("Gym and dinner."),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/search Python"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_search"
    assert "Search results for: Python" in response.json()["reply_text"]
    assert "Learning Python backend today." in response.json()["reply_text"]
    assert "Gym and dinner." not in response.json()["reply_text"]


def test_telegram_search_requires_keyword(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/telegram/webhook",
        json=telegram_update("/search"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_search_invalid"
    assert response.json()["reply_text"] == (
        "Use /search keyword to search your journal entries."
    )


def test_telegram_search_does_not_return_another_users_entries(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("Private Python note.", 111, "first"),
        headers=headers,
    )
    client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("Public work note.", 222, "second"),
        headers=headers,
    )

    response = client.post(
        "/telegram/webhook",
        json=telegram_update_for_user("/search Python", 222, "second"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["action"] == "command_search"
    assert response.json()["reply_text"] == "No journal entries found for: Python"


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
