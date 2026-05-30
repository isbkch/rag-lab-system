import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("MOCK_AI_URL", "http://mock-ai:9000")

from app.core import database as database_module  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models.lab import LabEvent, ScenarioRun  # noqa: F401,E402


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database_module.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[database_module.get_db] = override_get_db
    app.dependency_overrides[get_settings] = get_settings
    monkeypatch.setattr("app.api.v1.endpoints.lab.run_scenario_task.delay", lambda *args: None)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
