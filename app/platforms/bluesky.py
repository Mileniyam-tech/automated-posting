import logging
from datetime import datetime, timezone
import httpx
from app.config import settings
from app.schemas import PlatformResult
from .base import BasePlatform

logger = logging.getLogger(__name__)


class BlueskyPlatform(BasePlatform):
    """
    Integration for Bluesky (AT Protocol) via XRPC endpoints.
    Docs: https://docs.bsky.app/docs/api/com/atproto/repo/create-record
    """

    def __init__(self):
        super().__init__(name="Bluesky")

    def is_configured(self) -> bool:
        return bool(
            settings.BLUESKY_HANDLE
            and settings.BLUESKY_APP_PASSWORD
            and not settings.BLUESKY_HANDLE.startswith("your_")
            and not settings.BLUESKY_HANDLE.startswith("mock")
        )

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        if not self.is_configured():
            if settings.ALLOW_MOCK_FALLBACK:
                return self.success_result(
                    posted_url="https://bsky.app/profile/dxoratech.bsky.social/post/3kqwe7890abc",
                    public_access=True
                )
            return self.failure_result("Authentication failed: Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD")

        pds_url = settings.BLUESKY_PDS_URL.rstrip("/")

        try:
            # 1. Create AT Protocol Session
            session_resp = await client.post(
                f"{pds_url}/xrpc/com.atproto.server.createSession",
                json={
                    "identifier": settings.BLUESKY_HANDLE,
                    "password": settings.BLUESKY_APP_PASSWORD
                },
                timeout=settings.HTTP_TIMEOUT_SECONDS
            )

            if session_resp.status_code != 200:
                return self.failure_result(f"Bluesky Auth Failed (HTTP {session_resp.status_code}): {session_resp.text}")

            session_data = session_resp.json()
            access_jwt = session_data.get("accessJwt")
            did = session_data.get("did")
            handle = session_data.get("handle", settings.BLUESKY_HANDLE)

            # 2. Publish record to repo
            post_payload = {
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
            }

            headers = {
                "Authorization": f"Bearer {access_jwt}",
                "Content-Type": "application/json"
            }

            post_resp = await client.post(
                f"{pds_url}/xrpc/com.atproto.repo.createRecord",
                json=post_payload,
                headers=headers,
                timeout=settings.HTTP_TIMEOUT_SECONDS
            )

            if post_resp.status_code in (200, 201):
                res_data = post_resp.json()
                uri = res_data.get("uri", "")
                rkey = uri.split("/")[-1] if "/" in uri else "post"
                posted_url = f"https://bsky.app/profile/{handle}/post/{rkey}"
                return self.success_result(posted_url=posted_url, public_access=True)

            return self.failure_result(f"Bluesky Post Failed (HTTP {post_resp.status_code}): {post_resp.text}")

        except httpx.TimeoutException:
            return self.failure_result("Connection timeout while contacting Bluesky PDS API")
        except Exception as exc:
            return self.failure_result(f"Bluesky Error: {str(exc)}")
