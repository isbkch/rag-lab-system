from celery import Celery

from app.core.config import settings


def create_celery_app() -> Celery:
    celery_app = Celery(
        "failure_lab",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.lab"],
    )
    celery_app.conf.update(
        task_routes={"app.tasks.lab.*": {"queue": "lab"}},
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        result_expires=3600,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        worker_concurrency=2,
    )
    return celery_app


celery = create_celery_app()
