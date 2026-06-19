import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class TelegramBotApiClient:
    def __init__(self, bot_token: str, timeout_seconds: float = 10.0) -> None:
        self.bot_token = bot_token
        self.timeout_seconds = timeout_seconds

    def send_message(self, chat_id: int, text: str) -> None:
        if not self.bot_token or not text:
            return

        request = self._build_send_message_request(chat_id, text)
        try:
            with urlopen(request, timeout=self.timeout_seconds):
                return
        except (HTTPError, URLError, TimeoutError) as error:
            logger.warning(
                "Telegram reply send failed",
                extra={"chat_id": str(chat_id), "error": str(error)},
            )

    def _build_send_message_request(self, chat_id: int, text: str) -> Request:
        payload = urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        return Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
