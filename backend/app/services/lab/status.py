import httpx
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.metrics import get_metrics_collector


async def get_component_status(db: Session, settings: Settings) -> dict[str, dict]:
    components = {
        "postgres": await _check_postgres(db),
        "redis": await _check_redis(settings.REDIS_URL, settings),
        "chromadb": await _check_http(
            f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/heartbeat",
            settings,
        ),
        "mock_ai": await _check_http(f"{settings.MOCK_AI_URL}/health", settings),
        "worker_queue": await _check_queue(settings.REDIS_URL, settings),
    }
    metrics = get_metrics_collector()
    for component, detail in components.items():
        metrics.update_dependency_status(component, detail.get("status") == "healthy")
    return components


async def _check_postgres(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}


async def _check_redis(redis_url: str, settings: Settings) -> dict:
    client = redis.from_url(redis_url)
    try:
        await client.ping()
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}
    finally:
        await client.aclose()


async def _check_queue(redis_url: str, settings: Settings) -> dict:
    client = redis.from_url(redis_url)
    try:
        backlog = await client.llen("lab")
        return {"status": "healthy", "backlog": backlog}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc), "backlog": None}
    finally:
        await client.aclose()


async def _check_http(url: str, settings: Settings) -> dict:
    try:
        async with httpx.AsyncClient(
            timeout=settings.DEPENDENCY_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            return {"status": "healthy", "detail": payload}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}
