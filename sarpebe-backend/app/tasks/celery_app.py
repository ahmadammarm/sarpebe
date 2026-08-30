from celery import Celery
from app.config import settings

celery_app = Celery(
    "sarpebe_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.generation_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
    # Best practice for async DB code inside Celery: use worker_pool=solo or threads
    # if using Windows, though prefork works on Linux.
)
