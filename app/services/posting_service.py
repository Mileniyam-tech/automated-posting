import asyncio
import logging
from typing import List
import httpx

from app.schemas import PlatformResult, PostingResponse
from app.platforms import (
    BasePlatform,
    TelegramPlatform,
    DiscordPlatform,
    SlackPlatform,
    MastodonPlatform,
    BlueskyPlatform,
    HuggingFacePlatform,
)

logger = logging.getLogger(__name__)


class PostingService:
    def __init__(self, platforms: List[BasePlatform] = None):
        if platforms is not None:
            self.platforms = platforms
        else:
            self.platforms = [
                TelegramPlatform(),
                DiscordPlatform(),
                SlackPlatform(),
                MastodonPlatform(),
                BlueskyPlatform(),
                HuggingFacePlatform(),
            ]

    async def _safe_post(
        self,
        platform: BasePlatform,
        message: str,
        client: httpx.AsyncClient
    ) -> PlatformResult:
        try:
            return await platform.post_message(message=message, client=client)
        except Exception as exc:
            logger.exception(f"Error publishing to {platform.name}: {exc}")
            return platform.failure_result(f"Error: {str(exc)}")

    async def broadcast_message(self, message: str) -> PostingResponse:
        """
        Broadcasts the validated message to all registered platforms concurrently.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            tasks = [
                self._safe_post(platform, message, client)
                for platform in self.platforms
            ]
            
            # Run all platform posts concurrently
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: List[PlatformResult] = []
        for platform, res in zip(self.platforms, raw_results):
            if isinstance(res, Exception):
                logger.error(f"Task exception for {platform.name}: {res}")
                results.append(platform.failure_result(str(res)))
            elif isinstance(res, PlatformResult):
                results.append(res)
            else:
                results.append(platform.failure_result("Unexpected return type from platform"))

        overall_success = any(r.status == "success" for r in results)

        return PostingResponse(
            success=overall_success,
            results=results
        )
