from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.report import Report


class ReportRepository(ABC):
    @abstractmethod
    def get_for_user_period(
        self,
        user_id: UUID,
        report_type: str,
        period_start: date,
        period_end: date,
    ) -> Report | None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
