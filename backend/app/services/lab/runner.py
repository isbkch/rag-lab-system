import asyncio
import time
from typing import Any

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.metrics import get_metrics_collector
from app.services.lab.catalog import get_scenario
from app.services.lab.mock_ai_client import MockAIClient
from app.services.lab.repository import LabRepository


async def run_scenario(
    db: Session,
    settings: Settings,
    run_id: str,
    scenario_id: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo = LabRepository(db)
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    merged_parameters = {**scenario.default_parameters, **(parameters or {})}
    started = time.time()
    metrics = get_metrics_collector()
    repo.mark_run_started(run_id)
    repo.record_event(
        run_id,
        scenario.component,
        "info",
        f"Started scenario {scenario_id}",
        merged_parameters,
    )

    try:
        summary = await _execute_scenario(db, settings, scenario_id, merged_parameters)
        repo.record_event(
            run_id,
            scenario.component,
            "info",
            f"Completed scenario {scenario_id}",
            summary,
        )
        repo.mark_run_completed(run_id, summary)
        metrics.record_scenario_run(
            scenario_id=scenario_id,
            status="completed",
            duration=time.time() - started,
        )
        return summary
    except Exception as exc:
        repo.record_event(run_id, scenario.component, "error", str(exc))
        repo.mark_run_failed(run_id, str(exc))
        metrics.record_scenario_run(
            scenario_id=scenario_id,
            status="failed",
            duration=time.time() - started,
        )
        raise


async def _execute_scenario(
    db: Session,
    settings: Settings,
    scenario_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    if scenario_id in {"mock_ai_timeout", "mock_ai_500"}:
        client = MockAIClient(
            settings.MOCK_AI_URL, timeout_seconds=settings.DEPENDENCY_TIMEOUT_SECONDS
        )
        mode = str(parameters.get("mode", "error"))
        await client.set_mode(mode)
        response = await client.complete(str(parameters.get("prompt", "demo")))
        return {"mock_ai_response": response}

    if scenario_id == "redis_unavailable":
        client = redis.from_url(str(parameters["redis_url"]))
        try:
            await client.ping()
            return {"redis": "reachable"}
        finally:
            await client.aclose()

    if scenario_id == "queue_backlog":
        sleep_seconds = min(float(parameters.get("sleep_seconds", 5)), 30.0)
        await asyncio.sleep(sleep_seconds)
        return {"slept_seconds": sleep_seconds}

    if scenario_id == "postgres_pool_pressure":
        queries = min(int(parameters.get("queries", 5)), 25)
        for _ in range(queries):
            db.execute(text("SELECT 1"))
        return {"queries": queries}

    if scenario_id == "vector_latency":
        delay_seconds = min(float(parameters.get("delay_seconds", 2)), 10.0)
        await asyncio.sleep(delay_seconds)
        return {"delayed_seconds": delay_seconds}

    if scenario_id == "stale_health":
        return {
            "lesson": (
                "The root liveness endpoint can be healthy while dependency "
                "status is degraded."
            )
        }

    raise ValueError(f"Unhandled scenario: {scenario_id}")
