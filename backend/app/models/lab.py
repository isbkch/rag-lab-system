import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class ScenarioRun(Base):
    """A single execution of a failure scenario."""

    __tablename__ = "scenario_runs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    scenario_id = Column(String(100), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="queued", index=True)
    parameters = Column(JSON, nullable=False, default=dict)
    summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    events = relationship(
        "LabEvent", back_populates="run", cascade="all, delete-orphan"
    )


class LabEvent(Base):
    """Timestamped event emitted while a scenario is queued or running."""

    __tablename__ = "lab_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    run_id = Column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=True
    )
    component = Column(String(100), nullable=False, index=True)
    severity = Column(String(30), nullable=False, default="info", index=True)
    message = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    run = relationship("ScenarioRun", back_populates="events")
