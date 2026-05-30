from app.services.lab.repository import LabRepository


def test_create_run_and_event(db_session):
    repo = LabRepository(db_session)

    run = repo.create_run("mock_ai_500", {"mode": "error"})
    repo.record_event(str(run.id), "mock-ai", "error", "mock AI returned 500")

    runs = repo.list_runs(limit=10)
    events = repo.list_events(limit=10)

    assert len(runs) == 1
    assert runs[0].scenario_id == "mock_ai_500"
    assert runs[0].status == "queued"
    assert runs[0].parameters == {"mode": "error"}
    assert len(events) == 1
    assert events[0].component == "mock-ai"
    assert events[0].severity == "error"
    assert events[0].message == "mock AI returned 500"


def test_mark_run_lifecycle(db_session):
    repo = LabRepository(db_session)

    run = repo.create_run("queue_backlog", {"jobs": 3})
    repo.mark_run_started(str(run.id))
    repo.mark_run_completed(str(run.id), {"processed": 3})

    saved = repo.list_runs(limit=1)[0]
    assert saved.status == "completed"
    assert saved.summary == {"processed": 3}
    assert saved.started_at is not None
    assert saved.completed_at is not None
