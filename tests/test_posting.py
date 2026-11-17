import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"

        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_successful_posting_flow():
    # Make sure app state is initialized as in lifespan
    from app.services.posting_service import PostingService
    app.state.posting_service = PostingService()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
        response = await client.post("/posting", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert isinstance(data["success"], bool)
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) >= 5

        # Check required fields for each platform result
        required_fields = {"platform", "status", "posted_url", "public_access", "date", "time", "error"}
        for item in data["results"]:
            assert required_fields.issubset(item.keys())
            assert item["status"] in ("success", "failed")
            if item["status"] == "success":
                assert item["posted_url"] is not None
                assert item["date"] is not None
                assert item["time"] is not None
                assert item["error"] is None
            else:
                assert item["error"] is not None


@pytest.mark.asyncio
async def test_posting_validation_error_too_long():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        long_message = "A" * 190 + " https://example.com"
        response = await client.post("/posting", json={"message": long_message})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "exceeds the maximum limit of 200 characters" in str(data)


@pytest.mark.asyncio
async def test_posting_validation_error_missing_cta():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/posting", json={"message": "Simple message without any link."})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "Message must contain exactly one Call-To-Action (CTA) link" in str(data)


@pytest.mark.asyncio
async def test_posting_validation_error_multiple_ctas():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/posting",
            json={"message": "Visit https://first.com or https://second.com for deals."}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "Message must contain exactly one Call-To-Action (CTA) link, but 2 were found" in str(data)
