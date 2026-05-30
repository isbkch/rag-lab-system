import httpx
import pytest

from app.services.lab.mock_ai_client import MockAIClient, MockAIError


@pytest.mark.asyncio
async def test_mock_ai_client_returns_text():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "mock response", "mode": "normal"})

    transport = httpx.MockTransport(handler)
    client = MockAIClient(
        "http://mock-ai:9000", timeout_seconds=0.1, transport=transport
    )

    response = await client.complete("hello")

    assert response["text"] == "mock response"
    assert response["mode"] == "normal"


@pytest.mark.asyncio
async def test_mock_ai_client_converts_500_to_domain_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "forced failure"})

    transport = httpx.MockTransport(handler)
    client = MockAIClient(
        "http://mock-ai:9000", timeout_seconds=0.1, transport=transport
    )

    with pytest.raises(MockAIError) as exc:
        await client.complete("hello")

    assert "500" in str(exc.value)


@pytest.mark.asyncio
async def test_mock_ai_client_converts_timeout_to_domain_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow dependency")

    transport = httpx.MockTransport(handler)
    client = MockAIClient(
        "http://mock-ai:9000", timeout_seconds=0.1, transport=transport
    )

    with pytest.raises(MockAIError) as exc:
        await client.complete("hello")

    assert "timeout" in str(exc.value).lower()
