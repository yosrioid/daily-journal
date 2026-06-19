from collections import Counter
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.application.dto.telegram import TelegramMessagePayload, TelegramWebhookResult
from app.application.services.journal_service import JournalService
from app.application.services.mood_service import MoodService
from app.application.services.report_service import ReportService
from app.application.services.user_service import UserService
from app.domain.entities.journal_entry import JournalEntry
from app.domain.entities.user import User
from app.shared.exceptions import NotFoundError

START_REPLY = (
    "Daily Journal is active.\n"
    "Send any message to save it as your journal entry.\n"
    "Use /weekly to generate this week's report.\n"
    "Use /monthly to generate this month's report."
)
HELP_REPLY = (
    "Available commands:\n"
    "/start - Register and show basic usage.\n"
    "/help - Show available commands.\n"
    "/today - Show today's journal entries.\n"
    "/weekly - Generate this week's report.\n"
    "/monthly - Generate this month's report.\n"
    "/mood - Show your mood summary.\n"
    "/timezone Area/City - Show or update your timezone.\n"
    "/search keyword - Search your journal entries.\n"
    "/delete_last - Delete your latest journal entry."
)


class TelegramService:
    def __init__(
        self,
        user_service: UserService,
        journal_service: JournalService,
        mood_service: MoodService,
        report_service: ReportService,
    ) -> None:
        self.user_service = user_service
        self.journal_service = journal_service
        self.mood_service = mood_service
        self.report_service = report_service

    def handle_message(self, message: TelegramMessagePayload) -> TelegramWebhookResult:
        user = self.user_service.resolve_telegram_user(
            telegram_user_id=message.user.telegram_user_id,
            telegram_username=message.user.telegram_username,
            first_name=message.user.first_name,
            last_name=message.user.last_name,
        )

        text = message.text.strip() if message.text else ""
        if not text:
            return TelegramWebhookResult(
                ok=True,
                action="ignored",
                reply_text=None,
                user_id=user.id,
            )

        if text == "/start":
            return TelegramWebhookResult(
                ok=True,
                action="command_start",
                reply_text=START_REPLY,
                user_id=user.id,
            )

        if text == "/help":
            return TelegramWebhookResult(
                ok=True,
                action="command_help",
                reply_text=HELP_REPLY,
                user_id=user.id,
            )

        if text == "/today":
            entry_date = self._entry_date(message.unix_timestamp, user.timezone)
            entries = self.journal_service.list_entries_for_user_by_date(
                user_id=user.id,
                entry_date=entry_date,
            )
            return TelegramWebhookResult(
                ok=True,
                action="command_today",
                reply_text=self._entries_reply("Today's journal entries", entries),
                user_id=user.id,
            )

        if text == "/delete_last":
            try:
                entry = self.journal_service.delete_latest_entry_for_user(user.id)
            except NotFoundError:
                return TelegramWebhookResult(
                    ok=True,
                    action="command_delete_last_empty",
                    reply_text="No journal entries to delete.",
                    user_id=user.id,
                )

            return TelegramWebhookResult(
                ok=True,
                action="command_delete_last",
                reply_text=(
                    "Deleted latest journal entry: "
                    f"{entry.entry_date.isoformat()} - {self._snippet(entry.raw_text)}"
                ),
                user_id=user.id,
            )

        if text == "/weekly":
            report = self.report_service.generate_weekly_report(
                user_id=user.id,
                reference_date=self._entry_date(message.unix_timestamp, user.timezone),
            )
            return TelegramWebhookResult(
                ok=True,
                action="command_weekly",
                reply_text=report.summary,
                user_id=user.id,
            )

        if text == "/monthly":
            report = self.report_service.generate_monthly_report(
                user_id=user.id,
                reference_date=self._entry_date(message.unix_timestamp, user.timezone),
            )
            return TelegramWebhookResult(
                ok=True,
                action="command_monthly",
                reply_text=report.summary,
                user_id=user.id,
            )

        if text == "/mood":
            entries = self.journal_service.list_entries_for_user(user.id)
            return TelegramWebhookResult(
                ok=True,
                action="command_mood",
                reply_text=self._mood_reply(entries),
                user_id=user.id,
            )

        if text == "/timezone" or text.startswith("/timezone "):
            return self._handle_timezone_command(text, user)

        if text == "/search" or text.startswith("/search "):
            return self._handle_search_command(text, user.id)

        analysis = self.mood_service.analyze(message.text or "")
        entry = self.journal_service.create_entry(
            user_id=user.id,
            raw_text=message.text or "",
            entry_date=self._entry_date(message.unix_timestamp, user.timezone),
            mood_score=analysis.mood_score,
            mood_label=analysis.mood_label,
            tags=analysis.tags,
        )
        return TelegramWebhookResult(
            ok=True,
            action="journal_saved",
            reply_text="Journal saved.",
            user_id=user.id,
            journal_entry_id=entry.id,
        )

    def _entry_date(self, unix_timestamp: int, timezone: str) -> date:
        try:
            zone_info = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            zone_info = ZoneInfo("Asia/Jakarta")

        return datetime.fromtimestamp(unix_timestamp, tz=zone_info).date()

    def _handle_search_command(
        self,
        text: str,
        user_id: UUID,
    ) -> TelegramWebhookResult:
        keyword = text.removeprefix("/search").strip()
        if not keyword:
            return TelegramWebhookResult(
                ok=True,
                action="command_search_invalid",
                reply_text="Use /search keyword to search your journal entries.",
                user_id=user_id,
            )

        entries = self.journal_service.search_entries_for_user(user_id, keyword)
        return TelegramWebhookResult(
            ok=True,
            action="command_search",
            reply_text=self._search_reply(keyword, entries),
            user_id=user_id,
        )

    def _handle_timezone_command(
        self,
        text: str,
        user: User,
    ) -> TelegramWebhookResult:
        timezone = text.removeprefix("/timezone").strip()
        if not timezone:
            return TelegramWebhookResult(
                ok=True,
                action="command_timezone",
                reply_text=(
                    f"Current timezone: {user.timezone}\n"
                    "Use /timezone Area/City to update it."
                ),
                user_id=user.id,
            )

        try:
            updated_user = self.user_service.update_timezone(user, timezone)
        except ValueError:
            return TelegramWebhookResult(
                ok=True,
                action="command_timezone_invalid",
                reply_text=(
                    "Invalid timezone. Use an IANA timezone like Asia/Jakarta."
                ),
                user_id=user.id,
            )

        return TelegramWebhookResult(
            ok=True,
            action="command_timezone_updated",
            reply_text=f"Timezone updated to {updated_user.timezone}.",
            user_id=user.id,
        )

    def _search_reply(self, keyword: str, entries: list[JournalEntry]) -> str:
        if not entries:
            return f"No journal entries found for: {keyword}"

        lines = [f"Search results for: {keyword}"]
        for entry in entries[:5]:
            lines.append(
                f"- {entry.entry_date.isoformat()}: {self._snippet(entry.raw_text)}",
            )
        if len(entries) > 5:
            lines.append(f"And {len(entries) - 5} more entries.")
        return "\n".join(lines)

    def _entries_reply(self, title: str, entries: list[JournalEntry]) -> str:
        if not entries:
            return "No journal entries found for today."

        lines = [title]
        for entry in entries[:5]:
            lines.append(f"- {self._snippet(entry.raw_text)}")
        if len(entries) > 5:
            lines.append(f"And {len(entries) - 5} more entries.")
        return "\n".join(lines)

    def _mood_reply(self, entries: list[JournalEntry]) -> str:
        mood_scores = [
            entry.mood_score for entry in entries if entry.mood_score is not None
        ]
        if not mood_scores:
            return "No mood data available yet."

        mood_labels = [
            entry.mood_label for entry in entries if entry.mood_label is not None
        ]
        average = round(sum(mood_scores) / len(mood_scores), 1)
        lines = [
            "Mood Summary",
            f"Entries with mood: {len(mood_scores)}",
            f"Average mood: {average}/10",
            f"Lowest mood: {min(mood_scores)}/10",
            f"Highest mood: {max(mood_scores)}/10",
        ]
        if mood_labels:
            common_label = Counter(mood_labels).most_common(1)[0][0]
            lines.append(f"Most common mood: {common_label}")
        return "\n".join(lines)

    def _snippet(self, raw_text: str) -> str:
        normalized = " ".join(raw_text.split())
        if len(normalized) <= 80:
            return normalized
        return f"{normalized[:77]}..."
