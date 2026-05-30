def test_celery_imports_lab_tasks():
    from app.celery_app import celery
    import app.tasks.lab  # noqa: F401

    assert "app.tasks.lab.run_scenario" in celery.tasks
