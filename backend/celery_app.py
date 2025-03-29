from celery import Celery
from asgiref.sync import async_to_sync

celery_app = Celery(
    "my_app", broker="redis://redis:6379/0", backend="redis://redis:6379/0"
)  # Replace with your broker URL


@celery_app.task
def send_reset_password_email_task(email: str, token: str):
    from backend.services.email_service import (
        send_reset_password_email,
    )  # Import inside the task

    async_to_sync(send_reset_password_email)(email, token)
