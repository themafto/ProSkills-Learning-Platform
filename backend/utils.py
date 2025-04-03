import os
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.models import OurUsers
from backend.roles import UserRole

# Password encryption utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Create password hash from plain text password"""
    return pwd_context.hash(password)


def create_admin_user(db: Session) -> Optional[OurUsers]:
    """
    Create a specific admin user if it doesn't exist yet

    Returns:
        The admin user (if created or found)
    """
    # Get admin credentials from environment variables or use default values
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "adminpassword")
    admin_first_name = os.getenv("ADMIN_FIRST_NAME", "Admin")
    admin_last_name = os.getenv("ADMIN_LAST_NAME", "User")

    # Check if this specific admin user already exists
    admin_user = db.query(OurUsers).filter(OurUsers.email == admin_email).first()

    if admin_user:
        print(f"Admin user {admin_email} already exists.")
        return admin_user

    # Create a new admin user
    hashed_password = get_password_hash(admin_password)

    new_admin = OurUsers(
        email=admin_email,
        hashed_password=hashed_password,
        first_name=admin_first_name,
        last_name=admin_last_name,
        is_active=True,
        role=UserRole.ADMIN.value,
    )

    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"Created admin user with email: {admin_email}")
        return new_admin
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {str(e)}")
        return None
