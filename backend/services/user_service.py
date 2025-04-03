from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.ourusers import OurUsers


def check_if_user_exists(db: Session, email: str, create_user_request=None):
    if email:  # Перевіряємо email, тільки якщо він переданий
        existing_email = db.query(OurUsers).filter(OurUsers.email == email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use."
            )
