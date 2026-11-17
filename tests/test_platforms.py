import pytest
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.services.posting_service import PostingService


class MockSucceedingPlatform(BasePlatform):
    def __init__(self, name: str):
        super().__init__(name=name)

    def is_configured(self) -> bool:
        return True

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        return self.success_result(
            posted_url=f"https://{self.name.lower()}.com/post/999",
            public_access=True
        )


class MockFailingPlatform(BasePlatform):
    def __init__(self, name: str, error_message: str = "Authentication failed"):
        super().__init__(name=name)
        self.error_message = error_message

    def is_configured(self) -> bool:
        return True

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        return self.failure_result(self.error_message)


class MockCrashingPlatform(BasePlatform):
    def __init__(self, name: str):
        super().__init__(name=name)

    def is_configured(self) -> bool:
        return True

    async def post_message(self, message: str, client: httpx.AsyncClient) -> PlatformResult:
        raise ConnectionResetError("Remote server forcibly closed an existing connection")


@pytest.mark.asyncio
async def test_independent_platform_failure_resilience():
    """
    Validates Requirement 3.A:
    - Handle each platform independently.
    - If one platform fails, continue posting to the remaining platforms.
    """
    platform_a = MockSucceedingPlatform("Platform A")
    platform_b = MockFailingPlatform("Platform B", error_message="Authentication failed")
    platform_c = MockCrashingPlatform("Platform C")
    platform_d = MockSucceedingPlatform("Platform D")

    service = PostingService(platforms=[platform_a, platform_b, platform_c, platform_d])
    
    response = await service.broadcast_message(
        "Check out our latest business platform and grow your online visibility. https://example.com"
    )

    assert response.success is True
    assert len(response.results) == 4

    # Platform A succeeded
    res_a = next(r for r in response.results if r.platform == "Platform A")
    assert res_a.status == "success"
    assert res_a.posted_url == "https://platform a.com/post/999"
    assert res_a.public_access is True
    assert res_a.error is None

    # Platform B failed gracefully with authentication error
    res_b = next(r for r in response.results if r.platform == "Platform B")
    assert res_b.status == "failed"
    assert res_b.posted_url is None
    assert res_b.public_access is False
    assert "Authentication failed" in res_b.error

    # Platform C crashed with unhandled exception, caught safely by service boundary
    res_c = next(r for r in response.results if r.platform == "Platform C")
    assert res_c.status == "failed"
    assert "Remote server forcibly closed" in res_c.error

    # Platform D still succeeded despite previous errors
    res_d = next(r for r in response.results if r.platform == "Platform D")
    assert res_d.status == "success"
    assert res_d.posted_url == "https://platform d.com/post/999"
