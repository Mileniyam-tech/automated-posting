import logging
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class SlackPlatform(BasePlatform):
    """
    Integration for Slack via official Slack Incoming Webhooks.
    Docs: https://api.slack.com/messaging/webhooks
    """

    def __init__(self):
        super().__init__(name="Slack")

    def is_configured(self) -> bool:
        webhook = settings.SLACK_WEBHOOK_URL
        return bool(
            webhook
            and webhook.startswith("https://hooks.slack.com/")
            and not "your_" in webhook
            and not "mock" in webhook
        )

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://dxora-tech.slack.com/archives/C06ABCD1234/p1709827364000100",
                    public_access=False
                )
            return self.failure_result("Authentication failed: Missing or invalid SLACK_WEBHOOK_URL")

        payload = {
            "text": message
        }

        try:
            response = await client.post(
                settings.SLACK_WEBHOOK_URL,
                json=payload,
                timeout=settings.HTTP_TIMEOUT_SECONDS
            )

            if response.status_code == 200 and response.text.strip().lower() == "ok":
                # Slack incoming webhooks publish to internal workspace channels
                posted_url = "https://app.slack.com/client"
                return self.success_result(posted_url=posted_url, public_access=False)

            return self.failure_result(f"Slack API Error (HTTP {response.status_code}): {response.text}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Slack API")
        except Exception as exc:
            return self.failure_result(f"Slack Error: {str(exc)}")
