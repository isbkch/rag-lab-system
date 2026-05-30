import asyncio
import random
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

Mode = Literal["normal", "slow", "error", "flaky"]


class ModeRequest(BaseModel):
    mode: Mode
    delay_seconds: float = Field(default=3.0, ge=0.0, le=30.0)
    failure_rate: float = Field(default=0.5, ge=0.0, le=1.0)


class CompletionRequest(BaseModel):
    prompt: str


class MockAIState:
    mode: Mode = "normal"
    delay_seconds: float = 3.0
    failure_rate: float = 0.5


state = MockAIState()
app = FastAPI(title="Failure Lab Mock AI", version="0.1.0")

requests_total = Counter(
    "mock_ai_requests_total", "Mock AI requests", ["endpoint", "mode", "status"]
)
request_duration = Histogram(
    "mock_ai_request_duration_seconds", "Mock AI request duration", ["endpoint", "mode"]
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": state.mode,
        "delay_seconds": state.delay_seconds,
        "failure_rate": state.failure_rate,
    }


@app.post("/admin/mode")
async def set_mode(request: ModeRequest):
    state.mode = request.mode
    state.delay_seconds = request.delay_seconds
    state.failure_rate = request.failure_rate
    return {
        "mode": state.mode,
        "delay_seconds": state.delay_seconds,
        "failure_rate": state.failure_rate,
    }


@app.post("/v1/complete")
async def complete(request: CompletionRequest):
    start_time = time.time()
    status = "success"
    try:
        if state.mode == "slow":
            await asyncio.sleep(state.delay_seconds)
        if state.mode == "error":
            status = "error"
            raise HTTPException(status_code=500, detail="mock AI forced error")
        if state.mode == "flaky" and random.random() < state.failure_rate:
            status = "error"
            raise HTTPException(status_code=503, detail="mock AI flaky failure")
        return {"text": f"mock response for {request.prompt}", "mode": state.mode}
    finally:
        requests_total.labels(
            endpoint="/v1/complete", mode=state.mode, status=status
        ).inc()
        request_duration.labels(endpoint="/v1/complete", mode=state.mode).observe(
            time.time() - start_time
        )


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
