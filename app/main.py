from fastapi import FastAPI

from app.infrastructure.telegram.bot_api import TelegramBotApiClient
from app.presentation.api.journal_router import router as journal_router
from app.presentation.api.report_router import router as report_router
from app.presentation.telegram.router import router as telegram_router
from app.shared.config import Settings, get_settings
from app.shared.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.app_env)

    app = FastAPI(
        title="Daily Journal",
        version="0.1.0",
        docs_url="/docs" if resolved_settings.is_development else None,
        redoc_url="/redoc" if resolved_settings.is_development else None,
    )
    app.state.settings = resolved_settings
    app.state.telegram_bot_client = TelegramBotApiClient(
        resolved_settings.telegram_bot_token,
    )

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": resolved_settings.app_env,
        }

    app.include_router(journal_router)
    app.include_router(report_router)
    app.include_router(telegram_router)

    return app


app = create_app()
