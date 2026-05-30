from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.lab.catalog import get_scenario, list_scenarios
from app.services.lab.repository import LabRepository
from app.services.lab.status import get_component_status
from app.tasks.lab import run_scenario as run_scenario_task

router = APIRouter()


class RunScenarioRequest(BaseModel):
    parameters: dict[str, Any] | None = None

    model_config = {"extra": "allow"}

    def merged_parameters(self) -> dict[str, Any]:
        payload = dict(self.model_extra or {})
        if self.parameters:
            payload.update(self.parameters)
        return payload


def _run_to_dict(run) -> dict[str, Any]:
    return {
        "id": run.id,
        "scenario_id": run.scenario_id,
        "status": run.status,
        "parameters": run.parameters or {},
        "summary": run.summary or {},
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def _event_to_dict(event) -> dict[str, Any]:
    return {
        "id": event.id,
        "run_id": event.run_id,
        "component": event.component,
        "severity": event.severity,
        "message": event.message,
        "metadata": event.metadata_ or {},
        "created_at": event.created_at.isoformat(),
    }


@router.get("/scenarios")
async def scenarios():
    return {"scenarios": list_scenarios()}


@router.post("/scenarios/{scenario_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_scenario(
    scenario_id: str,
    request: RunScenarioRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown scenario")

    repo = LabRepository(db)
    parameters = {**scenario.default_parameters, **request.merged_parameters()}
    run = repo.create_run(scenario_id, parameters)
    repo.record_event(str(run.id), "queue", "info", "Scenario queued")
    run_scenario_task.delay(str(run.id), scenario_id, parameters)
    response.status_code = status.HTTP_202_ACCEPTED
    return _run_to_dict(run)


@router.get("/runs")
async def recent_runs(limit: int = 25, db: Session = Depends(get_db)):
    repo = LabRepository(db)
    return {"runs": [_run_to_dict(run) for run in repo.list_runs(limit=limit)]}


@router.get("/events")
async def recent_events(
    limit: int = 50, run_id: str | None = None, db: Session = Depends(get_db)
):
    repo = LabRepository(db)
    return {
        "events": [
            _event_to_dict(event)
            for event in repo.list_events(limit=limit, run_id=run_id)
        ]
    }


@router.get("/status")
async def lab_status(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    components = await get_component_status(db, settings)
    degraded = [
        name for name, detail in components.items() if detail.get("status") != "healthy"
    ]
    return {
        "status": "degraded" if degraded else "healthy",
        "components": components,
        "degraded_components": degraded,
    }
