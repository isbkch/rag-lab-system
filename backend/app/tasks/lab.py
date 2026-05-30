import asyncio

from app.celery_app import celery
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.lab.runner import run_scenario as run_scenario_async


@celery.task(name="app.tasks.lab.run_scenario")
def run_scenario(run_id: str, scenario_id: str, parameters: dict | None = None) -> dict:
    db = SessionLocal()
    try:
        return asyncio.run(
            run_scenario_async(
                db=db,
                settings=get_settings(),
                run_id=run_id,
                scenario_id=scenario_id,
                parameters=parameters or {},
            )
        )
    finally:
        db.close()
