from datetime import date, datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.services.report_service import ReportService
from app.domain.entities.report import Report
from app.domain.entities.user import User
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.journal_repository import (
    SQLAlchemyJournalRepository,
)
from app.infrastructure.repositories.report_repository import SQLAlchemyReportRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.shared.config import Settings
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportResponse(BaseModel):
    id: UUID
    report_type: str
    period_start: date
    period_end: date
    mood_average: float | None
    mood_min: int | None
    mood_max: int | None
    summary: str | None
    dominant_topics: list[str] | None
    positive_patterns: list[str] | None
    negative_patterns: list[str] | None
    key_events: list[str] | None
    lessons_learned: list[str] | None
    recommendations: list[str] | None
    created_at: datetime
    updated_at: datetime


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
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_report_service(
    session: Annotated[Session, Depends(get_session)],
) -> ReportService:
    user_repository = SQLAlchemyUserRepository(session)
    journal_repository = SQLAlchemyJournalRepository(session)
    report_repository = SQLAlchemyReportRepository(session)
    return ReportService(journal_repository, report_repository, user_repository)


@router.post(
    "/weekly",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_internal_api_token)],
)
def generate_weekly_report(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    reference_date: Annotated[date | None, Query()] = None,
) -> ReportResponse:
    try:
        report = report_service.generate_weekly_report(
            user_id=current_user.id,
            reference_date=reference_date or local_today(current_user.timezone),
        )
    except NotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    session.commit()
    return to_report_response(report)


@router.get(
    "/weekly",
    response_model=ReportResponse,
    dependencies=[Depends(verify_internal_api_token)],
)
def get_weekly_report(
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    reference_date: Annotated[date | None, Query()] = None,
) -> ReportResponse:
    report = report_service.get_weekly_report(
        user_id=current_user.id,
        reference_date=reference_date or local_today(current_user.timezone),
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly report not found",
        )
    return to_report_response(report)


@router.post(
    "/monthly",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_internal_api_token)],
)
def generate_monthly_report(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    reference_date: Annotated[date | None, Query()] = None,
) -> ReportResponse:
    try:
        report = report_service.generate_monthly_report(
            user_id=current_user.id,
            reference_date=reference_date or local_today(current_user.timezone),
        )
    except NotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    session.commit()
    return to_report_response(report)


@router.get(
    "/monthly",
    response_model=ReportResponse,
    dependencies=[Depends(verify_internal_api_token)],
)
def get_monthly_report(
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    reference_date: Annotated[date | None, Query()] = None,
) -> ReportResponse:
    report = report_service.get_monthly_report(
        user_id=current_user.id,
        reference_date=reference_date or local_today(current_user.timezone),
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found",
        )
    return to_report_response(report)


def local_today(timezone: str) -> date:
    try:
        zone_info = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone_info = ZoneInfo("Asia/Jakarta")
    return datetime.now(zone_info).date()


def to_report_response(report: Report) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        report_type=report.report_type,
        period_start=report.period_start,
        period_end=report.period_end,
        mood_average=report.mood_average,
        mood_min=report.mood_min,
        mood_max=report.mood_max,
        summary=report.summary,
        dominant_topics=report.dominant_topics,
        positive_patterns=report.positive_patterns,
        negative_patterns=report.negative_patterns,
        key_events=report.key_events,
        lessons_learned=report.lessons_learned,
        recommendations=report.recommendations,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )
