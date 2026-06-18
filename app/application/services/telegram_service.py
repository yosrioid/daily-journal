from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.application.dto.telegram import TelegramMessagePayload, TelegramWebhookResult
from app.application.services.journal_service import JournalService
from app.application.services.mood_service import MoodService
from app.application.services.report_service import ReportService
from app.application.services.user_service import UserService

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
