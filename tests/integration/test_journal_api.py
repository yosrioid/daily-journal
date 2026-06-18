from collections.abc import Iterator
from datetime import date
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.database.models import JournalEntryModel
from app.infrastructure.database.session import get_session
from app.main import create_app
from app.presentation.api import journal_router
from app.shared.config import Settings


def build_client(db_session: Session) -> TestClient:
    app = create_app(Settings(INTERNAL_API_TOKEN="internal-test-token"))

    def override_get_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def auth_headers(telegram_user_id: int) -> dict[str, str]:
    return {
        "X-Internal-Api-Token": "internal-test-token",
        "X-Telegram-User-Id": str(telegram_user_id),
    }


def create_entry(
    client: TestClient,
    telegram_user_id: int,
    raw_text: str,
    entry_date: date,
) -> dict[str, object]:
    response = client.post(
        "/journal",
        json={"raw_text": raw_text, "entry_date": entry_date.isoformat()},
        headers=auth_headers(telegram_user_id),
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_get_journal_entry(db_session: Session) -> None:
    client = build_client(db_session)

    created = create_entry(
        client,
        telegram_user_id=1001,
        raw_text="Built the journal API today.",
        entry_date=date(2026, 6, 18),
    )
    response = client.get(f"/journal/{created['id']}", headers=auth_headers(1001))

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["raw_text"] == "Built the journal API today."
    assert response.json()["entry_date"] == "2026-06-18"


def test_create_journal_entry_stores_mood_and_tags(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.post(
        "/journal",
        json={
            "raw_text": "Today was produktif learning Python #Backend",
            "entry_date": "2026-06-18",
        },
        headers=auth_headers(1002),
    )

    assert response.status_code == 201
    assert response.json()["mood_score"] > 5
    assert response.json()["mood_label"] == "positive"
    assert response.json()["tags"] == ["backend", "learning"]


def test_journal_api_rejects_missing_internal_token(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.get("/journal", headers={"X-Telegram-User-Id": "1001"})

    assert response.status_code == 403


def test_journal_api_rejects_invalid_internal_token(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.get(
        "/journal",
        headers={
            "X-Internal-Api-Token": "wrong-token",
            "X-Telegram-User-Id": "1001",
        },
    )

    assert response.status_code == 403


def test_create_journal_entry_defaults_to_local_today(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(db_session)
    monkeypatch.setattr(
        journal_router,
        "local_today",
        lambda timezone: date(2026, 6, 19),
    )

    response = client.post(
        "/journal",
        json={"raw_text": "Entry without explicit date."},
        headers=auth_headers(1003),
    )

    assert response.status_code == 201
    assert response.json()["entry_date"] == "2026-06-19"


def test_journal_entries_are_isolated_by_telegram_user(db_session: Session) -> None:
    client = build_client(db_session)
    first_entry = create_entry(
        client,
        telegram_user_id=2001,
        raw_text="Private entry for first user.",
        entry_date=date(2026, 6, 18),
    )
    create_entry(
        client,
        telegram_user_id=2002,
        raw_text="Private entry for second user.",
        entry_date=date(2026, 6, 18),
    )

    blocked_response = client.get(
        f"/journal/{first_entry['id']}",
        headers=auth_headers(2002),
    )
    second_user_list = client.get("/journal", headers=auth_headers(2002))

    assert blocked_response.status_code == 404
    assert second_user_list.status_code == 200
    assert len(second_user_list.json()) == 1
    assert second_user_list.json()[0]["raw_text"] == "Private entry for second user."


def test_today_journal_entries_use_user_scope(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(db_session)
    monkeypatch.setattr(
        journal_router,
        "local_today",
        lambda timezone: date(2026, 6, 18),
    )
    create_entry(
        client,
        telegram_user_id=3001,
        raw_text="Today entry.",
        entry_date=date(2026, 6, 18),
    )
    create_entry(
        client,
        telegram_user_id=3001,
        raw_text="Yesterday entry.",
        entry_date=date(2026, 6, 17),
    )
    create_entry(
        client,
        telegram_user_id=3002,
        raw_text="Another user's today entry.",
        entry_date=date(2026, 6, 18),
    )

    response = client.get("/journal/today", headers=auth_headers(3001))

    assert response.status_code == 200
    assert [entry["raw_text"] for entry in response.json()] == ["Today entry."]


def test_search_journal_entries_filters_by_user(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(
        client,
        telegram_user_id=4001,
        raw_text="Learning FastAPI routing.",
        entry_date=date(2026, 6, 18),
    )
    create_entry(
        client,
        telegram_user_id=4001,
        raw_text="Workout and dinner.",
        entry_date=date(2026, 6, 18),
    )
    create_entry(
        client,
        telegram_user_id=4002,
        raw_text="FastAPI from another user.",
        entry_date=date(2026, 6, 18),
    )

    response = client.get(
        "/journal",
        params={"keyword": "fastapi"},
        headers=auth_headers(4001),
    )

    assert response.status_code == 200
    assert [entry["raw_text"] for entry in response.json()] == [
        "Learning FastAPI routing.",
    ]


def test_search_journal_entries_rejects_blank_keyword(db_session: Session) -> None:
    client = build_client(db_session)

    response = client.get(
        "/journal",
        params={"keyword": "   "},
        headers=auth_headers(4001),
    )

    assert response.status_code == 400


def test_delete_journal_entry_requires_ownership(db_session: Session) -> None:
    client = build_client(db_session)
    created = create_entry(
        client,
        telegram_user_id=5001,
        raw_text="Entry to delete.",
        entry_date=date(2026, 6, 18),
    )

    blocked_response = client.delete(
        f"/journal/{created['id']}",
        headers=auth_headers(5002),
    )
    deleted_response = client.delete(
        f"/journal/{created['id']}",
        headers=auth_headers(5001),
    )

    assert blocked_response.status_code == 404
    assert deleted_response.status_code == 200
    assert deleted_response.json()["deleted"] is True
    assert db_session.get(JournalEntryModel, UUID(str(created["id"]))) is None


def test_delete_latest_journal_entry_deletes_only_current_user_entry(
    db_session: Session,
) -> None:
    client = build_client(db_session)
    create_entry(
        client,
        telegram_user_id=6001,
        raw_text="Older entry.",
        entry_date=date(2026, 6, 17),
    )
    latest_entry = create_entry(
        client,
        telegram_user_id=6001,
        raw_text="Latest entry.",
        entry_date=date(2026, 6, 18),
    )
    other_user_entry = create_entry(
        client,
        telegram_user_id=6002,
        raw_text="Other user latest entry.",
        entry_date=date(2026, 6, 19),
    )

    response = client.delete("/journal/latest", headers=auth_headers(6001))

    assert response.status_code == 200
    assert response.json()["entry"]["id"] == latest_entry["id"]
    assert db_session.get(JournalEntryModel, UUID(str(latest_entry["id"]))) is None
    assert db_session.get(JournalEntryModel, UUID(str(other_user_entry["id"])))
