from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.config import Settings


def test_health_check_returns_ok() -> None:
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
    }
