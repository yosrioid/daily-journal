from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.services.journal_service import JournalService
from app.application.services.mood_service import MoodService
from app.domain.entities.journal_entry import JournalEntry
from app.domain.entities.user import User
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.journal_repository import (
    SQLAlchemyJournalRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.shared.config import Settings
from app.shared.exceptions import NotFoundError, OwnershipError

router = APIRouter(prefix="/journal", tags=["journal"])


class CreateJournalEntryRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    entry_date: date | None = None


class JournalEntryResponse(BaseModel):
    id: UUID
    entry_date: date
    raw_text: str
    processed_text: str | None
    summary: str | None
    mood_score: int | None
    mood_label: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


class DeletedJournalEntryResponse(BaseModel):
    deleted: bool
    entry: JournalEntryResponse


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def verify_internal_api_token(
    settings: Annotated[Settings, Depends(get_app_settings)],
    internal_api_token: Annotated[
        str | None,
        Header(alias="X-Internal-Api-Token"),
    ] = None,
) -> None:
    if (
        not settings.internal_api_token
        or internal_api_token != settings.internal_api_token
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal API token",
        )


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    telegram_user_id: Annotated[int, Header(alias="X-Telegram-User-Id")],
) -> User:
    user_repository = SQLAlchemyUserRepository(session)
    user = user_repository.get_by_telegram_user_id(telegram_user_id)
    if user is not None:
        return user

    return user_repository.create_from_telegram(
        telegram_user_id=telegram_user_id,
        telegram_username=None,
        first_name=None,
        last_name=None,
        timezone="Asia/Jakarta",
    )


def get_journal_service(
    session: Annotated[Session, Depends(get_session)],
) -> JournalService:
    user_repository = SQLAlchemyUserRepository(session)
    journal_repository = SQLAlchemyJournalRepository(session)
    return JournalService(journal_repository, user_repository)


def get_mood_service() -> MoodService:
    return MoodService()


@router.get(
    "",
    response_model=list[JournalEntryResponse],
    dependencies=[Depends(verify_internal_api_token)],
)
def list_journal_entries(
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
    keyword: Annotated[str | None, Query(min_length=1)] = None,
) -> list[JournalEntryResponse]:
    try:
        if keyword is not None:
            entries = journal_service.search_entries_for_user(current_user.id, keyword)
        else:
            entries = journal_service.list_entries_for_user(current_user.id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [to_journal_entry_response(entry) for entry in entries]


@router.post(
    "",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_internal_api_token)],
)
def create_journal_entry(
    payload: CreateJournalEntryRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
    mood_service: Annotated[MoodService, Depends(get_mood_service)],
) -> JournalEntryResponse:
    try:
        analysis = mood_service.analyze(payload.raw_text)
        entry = journal_service.create_entry(
            user_id=current_user.id,
            raw_text=payload.raw_text,
            entry_date=payload.entry_date or local_today(current_user.timezone),
            mood_score=analysis.mood_score,
            mood_label=analysis.mood_label,
            tags=analysis.tags,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    session.commit()
    return to_journal_entry_response(entry)


@router.get(
    "/today",
    response_model=list[JournalEntryResponse],
    dependencies=[Depends(verify_internal_api_token)],
)
def list_today_journal_entries(
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> list[JournalEntryResponse]:
    entries = journal_service.list_entries_for_user_by_date(
        user_id=current_user.id,
        entry_date=local_today(current_user.timezone),
    )
    return [to_journal_entry_response(entry) for entry in entries]


@router.delete(
    "/latest",
    response_model=DeletedJournalEntryResponse,
    dependencies=[Depends(verify_internal_api_token)],
)
def delete_latest_journal_entry(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> DeletedJournalEntryResponse:
    try:
        entry = journal_service.delete_latest_entry_for_user(current_user.id)
    except NotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    session.commit()
    return DeletedJournalEntryResponse(
        deleted=True,
        entry=to_journal_entry_response(entry),
    )


@router.get(
    "/{entry_id}",
    response_model=JournalEntryResponse,
    dependencies=[Depends(verify_internal_api_token)],
)
def get_journal_entry(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalEntryResponse:
    try:
        entry = journal_service.get_entry_for_user(entry_id, current_user.id)
    except OwnershipError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return to_journal_entry_response(entry)


@router.delete(
    "/{entry_id}",
    response_model=DeletedJournalEntryResponse,
    dependencies=[Depends(verify_internal_api_token)],
)
def delete_journal_entry(
    entry_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> DeletedJournalEntryResponse:
    try:
        entry = journal_service.delete_entry_for_user(entry_id, current_user.id)
    except OwnershipError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    session.commit()
    return DeletedJournalEntryResponse(
        deleted=True,
        entry=to_journal_entry_response(entry),
    )


def local_today(timezone: str) -> date:
    try:
        zone_info = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone_info = ZoneInfo("Asia/Jakarta")

    return datetime.now(UTC).astimezone(zone_info).date()


def to_journal_entry_response(entry: JournalEntry) -> JournalEntryResponse:
    return JournalEntryResponse(
        id=entry.id,
        entry_date=entry.entry_date,
        raw_text=entry.raw_text,
        processed_text=entry.processed_text,
        summary=entry.summary,
        mood_score=entry.mood_score,
        mood_label=entry.mood_label,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )
