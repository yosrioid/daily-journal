from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.report import Report
from app.domain.interfaces.report_repository import ReportRepository
from app.infrastructure.database.models import ReportModel, json_list


class SQLAlchemyReportRepository(ReportRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_user_period(
        self,
        user_id: UUID,
        report_type: str,
        period_start: date,
        period_end: date,
    ) -> Report | None:
        model = self._get_model_for_user_period(
            user_id=user_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
        )
        return self._to_entity(model) if model is not None else None

    def save(
        self,
        user_id: UUID,
        report_type: str,
        period_start: date,
        period_end: date,
        mood_average: float | None,
        mood_min: int | None,
        mood_max: int | None,
        summary: str,
        dominant_topics: list[str],
        positive_patterns: list[str],
        negative_patterns: list[str],
        key_events: list[str],
        lessons_learned: list[str],
        recommendations: list[str],
    ) -> Report:
        model = self._get_model_for_user_period(
            user_id=user_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
        )
        if model is None:
            model = ReportModel(
                user_id=user_id,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
            )
            self.session.add(model)

        model.mood_average = mood_average
        model.mood_min = mood_min
        model.mood_max = mood_max
        model.summary = summary
        model.dominant_topics = dominant_topics
        model.positive_patterns = positive_patterns
        model.negative_patterns = negative_patterns
        model.key_events = key_events
        model.lessons_learned = lessons_learned
        model.recommendations = recommendations
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def _get_model_for_user_period(
        self,
        user_id: UUID,
        report_type: str,
        period_start: date,
        period_end: date,
    ) -> ReportModel | None:
        statement = select(ReportModel).where(
            ReportModel.user_id == user_id,
            ReportModel.report_type == report_type,
            ReportModel.period_start == period_start,
            ReportModel.period_end == period_end,
        )
        return self.session.scalar(statement)

    def _to_entity(self, model: ReportModel) -> Report:
        return Report(
            id=model.id,
            user_id=model.user_id,
            report_type=model.report_type,
            period_start=model.period_start,
            period_end=model.period_end,
            mood_average=model.mood_average,
            mood_min=model.mood_min,
            mood_max=model.mood_max,
            summary=model.summary,
            dominant_topics=json_list(model.dominant_topics),
            positive_patterns=json_list(model.positive_patterns),
            negative_patterns=json_list(model.negative_patterns),
            key_events=json_list(model.key_events),
            lessons_learned=json_list(model.lessons_learned),
            recommendations=json_list(model.recommendations),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
