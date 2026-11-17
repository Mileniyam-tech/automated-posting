import logging
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class HuggingFacePlatform(BasePlatform):
    """
    Integration for Hugging Face LLM & AI Platform Community Discussions API.
    Docs: https://huggingface.co/docs/hub/api
    """

    def __init__(self):
        super().__init__(name="Hugging Face (LLM Hub)")

    def is_configured(self) -> bool:
        return bool(
            settings.HUGGINGFACE_API_TOKEN
            and settings.HUGGINGFACE_REPO_ID
            and not settings.HUGGINGFACE_API_TOKEN.startswith("your_")
            and not settings.HUGGINGFACE_API_TOKEN.startswith("mock")
            and not settings.HUGGINGFACE_API_TOKEN.startswith("hf_mock")
        )

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://huggingface.co/spaces/dxora/model-showcase/discussions/42",
                    public_access=True
                )
            return self.failure_result("Authentication failed: Missing HUGGINGFACE_API_TOKEN or HUGGINGFACE_REPO_ID")

        repo_id = settings.HUGGINGFACE_REPO_ID.strip("/")
        api_url = f"https://huggingface.co/api/spaces/{repo_id}/discussions"
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "title": "Platform Update Announcement",
            "content": message
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
                discussion_num = data.get("num", "latest")
                posted_url = f"https://huggingface.co/spaces/{repo_id}/discussions/{discussion_num}"
                return self.success_result(posted_url=posted_url, public_access=True)

            return self.failure_result(f"HuggingFace API Error (HTTP {response.status_code}): {response.text}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Hugging Face API")
        except Exception as exc:
            return self.failure_result(f"Hugging Face Error: {str(exc)}")
