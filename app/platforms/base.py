import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import httpx
from app.schemas import PlatformResult

logger = logging.getLogger(__name__)


class BasePlatform(ABC):
    """Base class for all platform integrations."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if valid API credentials are present in the environment."""
        pass

    @abstractmethod
    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        """
        Executes the API request to publish the message on this specific platform.
        """
        pass

    def success_result(
        self,
        posted_url: str,
        public_access: bool = True,
        timestamp: Optional[datetime] = None
    ) -> PlatformResult:
        """Constructs a standard successful PlatformResult."""
        ts = timestamp or datetime.now()
        return PlatformResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=public_access,
            date=ts.strftime("%Y-%m-%d"),
            time=ts.strftime("%H:%M:%S"),
            error=None
        )

    def failure_result(self, error: str) -> PlatformResult:
        """Constructs a standard failed PlatformResult."""
        logger.warning(f"Platform '{self.name}' failed to publish: {error}")
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error
        )
