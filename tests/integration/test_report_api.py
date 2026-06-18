from collections.abc import Iterator
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_session
from app.main import create_app
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
) -> None:
    response = client.post(
        "/journal",
        json={"raw_text": raw_text, "entry_date": entry_date.isoformat()},
        headers=auth_headers(telegram_user_id),
    )
    assert response.status_code == 201


def test_generate_weekly_report_from_user_entries(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(
        client,
        5001,
        "Today was produktif learning Python #Backend",
        date(2026, 6, 15),
    )
    create_entry(
        client,
        5001,
        "Work stress at deadline #Work",
        date(2026, 6, 17),
    )
    create_entry(client, 5001, "Next week entry #Later", date(2026, 6, 22))
    create_entry(client, 5002, "Other user produktif #Private", date(2026, 6, 17))

    response = client.post(
        "/reports/weekly?reference_date=2026-06-18",
        headers=auth_headers(5001),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["report_type"] == "weekly"
    assert payload["period_start"] == "2026-06-15"
    assert payload["period_end"] == "2026-06-21"
    assert payload["mood_average"] == 5.0
    assert payload["mood_min"] == 3
    assert payload["mood_max"] == 7
    assert "You wrote 2 journal entries this week." in payload["summary"]
    assert "private" not in payload["dominant_topics"]
    assert payload["key_events"] == [
        "Today was produktif learning Python #Backend",
        "Work stress at deadline #Work",
    ]


def test_get_weekly_report_returns_generated_report(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(client, 5101, "Progress learning Python #Backend", date(2026, 6, 18))
    created = client.post(
        "/reports/weekly?reference_date=2026-06-18",
        headers=auth_headers(5101),
    )

    response = client.get(
        "/reports/weekly?reference_date=2026-06-18",
        headers=auth_headers(5101),
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]


def test_get_weekly_report_returns_404_when_missing(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(client, 5201, "Old note #Archive", date(2026, 6, 1))

    response = client.get(
        "/reports/weekly?reference_date=2026-06-18",
        headers=auth_headers(5201),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Weekly report not found"


def test_generate_monthly_report_from_user_entries(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(client, 5301, "Progress learning Python #Backend", date(2026, 6, 1))
    create_entry(client, 5301, "Work stress at deadline #Work", date(2026, 6, 18))
    create_entry(client, 5301, "July planning #Later", date(2026, 7, 1))
    create_entry(client, 5302, "Other user produktif #Private", date(2026, 6, 18))

    response = client.post(
        "/reports/monthly?reference_date=2026-06-18",
        headers=auth_headers(5301),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["report_type"] == "monthly"
    assert payload["period_start"] == "2026-06-01"
    assert payload["period_end"] == "2026-06-30"
    assert payload["mood_average"] == 5.0
    assert payload["mood_min"] == 3
    assert payload["mood_max"] == 7
    assert "You wrote 2 journal entries this month." in payload["summary"]
    assert "Mood trend: declining" in payload["summary"]
    assert "private" not in payload["dominant_topics"]
    assert payload["key_events"] == [
        "Progress learning Python #Backend",
        "Work stress at deadline #Work",
    ]


def test_get_monthly_report_returns_generated_report(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(client, 5401, "Progress learning Python #Backend", date(2026, 6, 18))
    created = client.post(
        "/reports/monthly?reference_date=2026-06-18",
        headers=auth_headers(5401),
    )

    response = client.get(
        "/reports/monthly?reference_date=2026-06-18",
        headers=auth_headers(5401),
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]


def test_get_monthly_report_returns_404_when_missing(db_session: Session) -> None:
    client = build_client(db_session)
    create_entry(client, 5501, "Old note #Archive", date(2026, 5, 1))

    response = client.get(
        "/reports/monthly?reference_date=2026-06-18",
        headers=auth_headers(5501),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Monthly report not found"
