import logging
from typing import Optional
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class TelegramPlatform(BasePlatform):
    """
    Integration for Telegram Messenger via official Telegram Bot API.
    Docs: https://core.telegram.org/bots/api#sendmessage
    """

    def __init__(self):
        super().__init__(name="Telegram")

    def is_configured(self) -> bool:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        return bool(token and chat_id and not token.startswith("your_") and not token.startswith("mock_"))

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://t.me/dxora_announcements/4082",
                    public_access=True
                )
            return self.failure_result("Authentication failed: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False
        }

        try:
            response = await client.post(url, json=payload, timeout=settings.HTTP_TIMEOUT_SECONDS)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("ok"):
                res = response_data.get("result", {})
                message_id = res.get("message_id")
                chat = res.get("chat", {})
                username = chat.get("username")

                if username:
                    posted_url = f"https://t.me/{username}/{message_id}"
                    public_access = True
                else:
                    raw_id = str(chat.get("id", ""))
                    clean_id = raw_id.replace("-100", "").replace("-", "")
                    posted_url = f"https://t.me/c/{clean_id}/{message_id}"
                    public_access = False

                return self.success_result(posted_url=posted_url, public_access=public_access)
            
            error_desc = response_data.get("description", f"HTTP {response.status_code}")
            return self.failure_result(f"Telegram API Error: {error_desc}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Telegram API")
        except Exception as exc:
            return self.failure_result(f"Telegram Error: {str(exc)}")
