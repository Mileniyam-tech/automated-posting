import logging
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class MastodonPlatform(BasePlatform):
    """
    Integration for Mastodon decentralized social network via REST API.
    Docs: https://docs.joinmastodon.org/methods/statuses/#create
    """

    def __init__(self):
        super().__init__(name="Mastodon")

    def is_configured(self) -> bool:
        token = settings.MASTODON_ACCESS_TOKEN
        return bool(token and not token.startswith("your_") and not token.startswith("mock_"))

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://mastodon.social/@dxora_tech/112093847561928374",
                    public_access=True
                )
            return self.failure_result("Authentication failed: Missing MASTODON_ACCESS_TOKEN")

        instance_url = settings.MASTODON_INSTANCE_URL.rstrip("/")
        api_url = f"{instance_url}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {settings.MASTODON_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "status": message,
            "visibility": "public"
        }

        try:
            response = await client.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=settings.HTTP_TIMEOUT_SECONDS
            )

            if response.status_code in (200, 201):
                data = response.json()
                posted_url = data.get("url") or f"{instance_url}/notice/{data.get('id')}"
                is_public = data.get("visibility") == "public"
                return self.success_result(posted_url=posted_url, public_access=is_public)

            error_msg = response.json().get("error", f"HTTP {response.status_code}: {response.text}")
            return self.failure_result(f"Mastodon API Error: {error_msg}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Mastodon API")
        except Exception as exc:
            return self.failure_result(f"Mastodon Error: {str(exc)}")
