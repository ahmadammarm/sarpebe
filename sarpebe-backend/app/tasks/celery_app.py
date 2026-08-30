from celery import Celery
from app.config import settings

# Fix for Upstash/Secure Redis requiring explicit SSL cert reqs
broker_url = settings.redis_url
if broker_url.startswith("rediss://") and "ssl_cert_reqs" not in broker_url:
    join_char = "&" if "?" in broker_url else "?"
    broker_url += f"{join_char}ssl_cert_reqs=CERT_NONE"

celery_app = Celery(
    "sarpebe_tasks",
    broker=broker_url,
    backend=broker_url,
    include=["app.tasks.generation_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
)
