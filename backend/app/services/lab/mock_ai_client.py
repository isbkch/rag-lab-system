from typing import Any

import httpx


class MockAIError(RuntimeError):
    """Raised when the mock AI service fails in a controlled way."""


class MockAIClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 0.5,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)
        self.transport = transport

    async def complete(self, prompt: str) -> dict[str, Any]:
        return await self._post("/v1/complete", {"prompt": prompt})

    async def set_mode(self, mode: str, **parameters: Any) -> dict[str, Any]:
        return await self._post("/admin/mode", {"mode": mode, **parameters})

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            try:
                response = await client.post(path, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as exc:
                raise MockAIError(f"Mock AI timeout calling {path}") from exc
            except httpx.HTTPStatusError as exc:
                raise MockAIError(
                    f"Mock AI returned HTTP {exc.response.status_code} for {path}"
                ) from exc
            except httpx.HTTPError as exc:
                raise MockAIError(f"Mock AI request failed for {path}: {exc}") from exc
