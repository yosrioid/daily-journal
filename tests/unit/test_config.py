from app.shared.config import Settings


def test_settings_default_to_development() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.database_url == "sqlite:///./daily_journal.db"
    assert settings.ai_provider == "none"
