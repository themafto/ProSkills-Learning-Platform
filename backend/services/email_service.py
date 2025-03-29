from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
import os

load_dotenv()


class EmailSchema(BaseModel):
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_FROM"),
    MAIL_PORT=int(os.getenv("SMTP_PORT")),
    MAIL_SERVER=os.getenv("SMTP_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True")
    == "True",  # Должно быть True/False
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False") == "True",  # Должно быть True/False
    USE_CREDENTIALS=True,
)


async def send_reset_password_email(email: EmailStr, token: str):
    link = f"{os.getenv('FRONTEND_URL')}/reset-password/{token}"
    message = MessageSchema(
        subject="Reset password",
        recipients=[email],
        body=f"Tap to link to reset password: {link}",
        subtype="plain",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
