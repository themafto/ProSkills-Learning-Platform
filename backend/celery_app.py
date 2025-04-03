import os

from asgiref.sync import async_to_sync
from celery import Celery

celery_app = Celery(
    "my_app",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)


@celery_app.task
def send_reset_password_email_task(email: str, token: str):
    from backend.services.email_service import (  # Import inside the task
        send_reset_password_email,
    )

    async_to_sync(send_reset_password_email)(email, token)
