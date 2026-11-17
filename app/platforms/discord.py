import logging
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class DiscordPlatform(BasePlatform):
    """
    Integration for Discord via official Discord Webhook API.
    Docs: https://discord.com/developers/docs/resources/webhook#execute-webhook
    """

    def __init__(self):
        super().__init__(name="Discord")

    def is_configured(self) -> bool:
        webhook = settings.DISCORD_WEBHOOK_URL
        return bool(
            webhook
            and webhook.startswith("https://discord.com/api/webhooks/")
            and not "your_" in webhook
            and not "mock" in webhook
        )

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://discord.com/channels/120987654321098765/120987654321098766/120987654321098767",
                    public_access=True
                )
            return self.failure_result("Authentication failed: Missing or invalid DISCORD_WEBHOOK_URL")

        # Discord webhook endpoint with wait=true returns the created message object
        webhook_url = f"{settings.DISCORD_WEBHOOK_URL}?wait=true"
        payload = {
            "content": message
        }

        try:
            response = await client.post(webhook_url, json=payload, timeout=settings.HTTP_TIMEOUT_SECONDS)
            if response.status_code in (200, 201):
                data = response.json()
                channel_id = data.get("channel_id")
                message_id = data.get("id")
                guild_id = data.get("guild_id", "@me")
                posted_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
                return self.success_result(posted_url=posted_url, public_access=True)

            error_text = response.text
            return self.failure_result(f"Discord API Error (HTTP {response.status_code}): {error_text}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Discord API")
        except Exception as exc:
            return self.failure_result(f"Discord Error: {str(exc)}")
