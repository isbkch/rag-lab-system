from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.lab import LabEvent, ScenarioRun


class LabRepository:
    """Database operations for scenario runs and lab events."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self, scenario_id: str, parameters: dict[str, Any] | None = None
    ) -> ScenarioRun:
        run = ScenarioRun(
            scenario_id=scenario_id,
            status="queued",
            parameters=parameters or {},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: str) -> ScenarioRun | None:
        return self.db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()

    def mark_run_started(self, run_id: str) -> ScenarioRun | None:
        run = self.get_run(run_id)
        if run is None:
            return None
        run.status = "running"
        run.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def mark_run_completed(
        self, run_id: str, summary: dict[str, Any] | None = None
    ) -> ScenarioRun | None:
        run = self.get_run(run_id)
        if run is None:
            return None
        run.status = "completed"
        run.summary = summary or {}
        run.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def mark_run_failed(self, run_id: str, error_message: str) -> ScenarioRun | None:
        run = self.get_run(run_id)
        if run is None:
            return None
        run.status = "failed"
        run.error_message = error_message
        run.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def record_event(
        self,
        run_id: str | None,
        component: str,
        severity: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> LabEvent:
        event = LabEvent(
            run_id=run_id,
            component=component,
            severity=severity,
            message=message,
            metadata_=metadata or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_runs(self, limit: int = 25) -> list[ScenarioRun]:
        return (
            self.db.query(ScenarioRun)
            .order_by(desc(ScenarioRun.created_at))
            .limit(limit)
            .all()
        )

    def list_events(
        self, limit: int = 50, run_id: str | None = None
    ) -> list[LabEvent]:
        query = self.db.query(LabEvent)
        if run_id:
            query = query.filter(LabEvent.run_id == run_id)
        return query.order_by(desc(LabEvent.created_at)).limit(limit).all()
