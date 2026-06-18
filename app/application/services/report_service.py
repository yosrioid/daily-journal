from collections import Counter
from datetime import date, timedelta
from uuid import UUID

from app.domain.entities.journal_entry import JournalEntry
from app.domain.entities.report import Report
from app.domain.interfaces.journal_repository import JournalRepository
from app.domain.interfaces.report_repository import ReportRepository
from app.domain.interfaces.user_repository import UserRepository
from app.shared.exceptions import NotFoundError

LIMITED_DATA_MESSAGE = (
    "Data is limited, so this report may not represent the full week."
)
WEEKLY_REPORT_TYPE = "weekly"


class ReportService:
    def __init__(
        self,
        journal_repository: JournalRepository,
        report_repository: ReportRepository,
        user_repository: UserRepository,
    ) -> None:
        self.journal_repository = journal_repository
        self.report_repository = report_repository
        self.user_repository = user_repository

    def get_weekly_report(
        self,
        user_id: UUID,
        reference_date: date,
    ) -> Report | None:
        self._ensure_user_exists(user_id)
        period_start, period_end = self.week_period(reference_date)
        return self.report_repository.get_for_user_period(
            user_id=user_id,
            report_type=WEEKLY_REPORT_TYPE,
            period_start=period_start,
            period_end=period_end,
        )

    def generate_weekly_report(
        self,
        user_id: UUID,
        reference_date: date,
    ) -> Report:
        self._ensure_user_exists(user_id)
        period_start, period_end = self.week_period(reference_date)
        entries = self.journal_repository.list_for_user_between(
            user_id=user_id,
            start_date=period_start,
            end_date=period_end,
        )
        mood_scores = [
            entry.mood_score for entry in entries if entry.mood_score is not None
        ]

        return self.report_repository.save(
            user_id=user_id,
            report_type=WEEKLY_REPORT_TYPE,
            period_start=period_start,
            period_end=period_end,
            mood_average=self._mood_average(mood_scores),
            mood_min=min(mood_scores) if mood_scores else None,
            mood_max=max(mood_scores) if mood_scores else None,
            summary=self._summary(entries, period_start, period_end),
            dominant_topics=self._dominant_topics(entries),
            positive_patterns=self._patterns(entries, minimum_score=7),
            negative_patterns=self._patterns(entries, maximum_score=4),
            key_events=self._key_events(entries),
            lessons_learned=self._lessons_learned(entries),
            recommendations=self._recommendations(entries),
        )

    def week_period(self, reference_date: date) -> tuple[date, date]:
        period_start = reference_date - timedelta(days=reference_date.weekday())
        return period_start, period_start + timedelta(days=6)

    def _summary(
        self,
        entries: list[JournalEntry],
        period_start: date,
        period_end: date,
    ) -> str:
        lines = [
            "Weekly Report",
            f"Period: {period_start.isoformat()} to {period_end.isoformat()}",
            f"Entries: You wrote {len(entries)} journal entries this week.",
        ]
        if len(entries) < 3:
            lines.append(LIMITED_DATA_MESSAGE)
        return "\n".join(lines)

    def _mood_average(self, mood_scores: list[int]) -> float | None:
        if not mood_scores:
            return None
        return round(sum(mood_scores) / len(mood_scores), 1)

    def _dominant_topics(self, entries: list[JournalEntry]) -> list[str]:
        counter: Counter[str] = Counter()
        for entry in entries:
            counter.update(entry.tags or [])
        return [topic for topic, _count in counter.most_common(5)]

    def _patterns(
        self,
        entries: list[JournalEntry],
        minimum_score: int | None = None,
        maximum_score: int | None = None,
    ) -> list[str]:
        matched_tags: Counter[str] = Counter()
        for entry in entries:
            if self._matches_score(entry, minimum_score, maximum_score):
                matched_tags.update(entry.tags or [])
        return [tag for tag, _count in matched_tags.most_common(5)]

    def _matches_score(
        self,
        entry: JournalEntry,
        minimum_score: int | None,
        maximum_score: int | None,
    ) -> bool:
        if entry.mood_score is None:
            return False
        if minimum_score is not None and entry.mood_score < minimum_score:
            return False
        if maximum_score is not None and entry.mood_score > maximum_score:
            return False
        return True

    def _key_events(self, entries: list[JournalEntry]) -> list[str]:
        return [self._snippet(entry.raw_text) for entry in entries[:5]]

    def _lessons_learned(self, entries: list[JournalEntry]) -> list[str]:
        return [
            self._snippet(entry.raw_text)
            for entry in entries
            if "learn" in entry.raw_text.lower() or "belajar" in entry.raw_text.lower()
        ][:5]

    def _recommendations(self, entries: list[JournalEntry]) -> list[str]:
        if not entries:
            return ["Keep journaling at least once this week."]
        if len(entries) < 3:
            return ["Add more entries before relying on weekly patterns."]
        return ["Review dominant topics and keep the next week focused."]

    def _snippet(self, raw_text: str) -> str:
        normalized = " ".join(raw_text.split())
        if len(normalized) <= 120:
            return normalized
        return f"{normalized[:117]}..."

    def _ensure_user_exists(self, user_id: UUID) -> None:
        if self.user_repository.get_by_id(user_id) is None:
            raise NotFoundError("User not found")
