from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.dto.telegram import TelegramMessagePayload, TelegramUserPayload
from app.application.services.journal_service import JournalService
from app.application.services.mood_service import MoodService
from app.application.services.report_service import ReportService
from app.application.services.telegram_service import TelegramService
from app.application.services.user_service import UserService
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.journal_repository import (
    SQLAlchemyJournalRepository,
)
from app.infrastructure.repositories.report_repository import SQLAlchemyReportRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.shared.config import Settings

router = APIRouter(prefix="/telegram", tags=["telegram"])


class TelegramUserSchema(BaseModel):
    id: int
    is_bot: bool | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class TelegramMessageSchema(BaseModel):
    message_id: int
    date: int
    text: str | None = None
    from_user: TelegramUserSchema = Field(alias="from")

    model_config = ConfigDict(populate_by_name=True)


class TelegramUpdateSchema(BaseModel):
    update_id: int
    message: TelegramMessageSchema | None = None


class TelegramWebhookResponse(BaseModel):
    ok: bool
    action: str
    reply_text: str | None = None
    journal_entry_id: str | None = None


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def build_telegram_service(session: Session) -> TelegramService:
    user_repository = SQLAlchemyUserRepository(session)
    journal_repository = SQLAlchemyJournalRepository(session)
    report_repository = SQLAlchemyReportRepository(session)
    user_service = UserService(user_repository)
    journal_service = JournalService(journal_repository, user_repository)
    report_service = ReportService(
        journal_repository,
        report_repository,
        user_repository,
    )
    return TelegramService(user_service, journal_service, MoodService(), report_service)


@router.post("/webhook")
def telegram_webhook(
    update: TelegramUpdateSchema,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    secret_token: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
) -> TelegramWebhookResponse:
    if (
        settings.telegram_webhook_secret
        and secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret",
        )

    if update.message is None:
        return TelegramWebhookResponse(ok=True, action="ignored")

    result = build_telegram_service(session).handle_message(
        TelegramMessagePayload(
            message_id=update.message.message_id,
            unix_timestamp=update.message.date,
            text=update.message.text,
            user=TelegramUserPayload(
                telegram_user_id=update.message.from_user.id,
                telegram_username=update.message.from_user.username,
                first_name=update.message.from_user.first_name,
                last_name=update.message.from_user.last_name,
            ),
        ),
    )
    session.commit()

    return TelegramWebhookResponse(
        ok=result.ok,
        action=result.action,
        reply_text=result.reply_text,
        journal_entry_id=(
            str(result.journal_entry_id) if result.journal_entry_id else None
        ),
    )
