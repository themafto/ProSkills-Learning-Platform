import hashlib
from datetime import timedelta, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status, Form

from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm


from backend.dependencies.getdb import get_db
from backend.models.ourusers import OurUsers
from backend.oauth2 import (
    bcrypt_context,
    authenticate_user,
    create_access_token,
    get_current_user_jwt,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.roles import UserRole
from backend.services.token_blacklist import add_to_blacklist

from backend.schemas.user import CreateUserRequest, UserResponse, UserLoginResponseAuth
from backend.services.security import generate_password_reset_token
from backend.services.user_service import check_if_user_exists
from backend.celery_app import send_reset_password_email_task

router = APIRouter(prefix="/auth", tags=["auth"])


### ROUTE FOR REGISTRATION ###
@router.get("/me", response_model=UserLoginResponseAuth)
async def get_info(current_user: dict = Depends(get_current_user_jwt)):
    return {
        "id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"],
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
):
    if access_token:
        # Add access token to blacklist with its remaining expiration time
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")
            if exp:
                current_time = datetime.now(timezone.utc).timestamp()
                remaining_time = int(exp - current_time)
                if remaining_time > 0:
                    add_to_blacklist(access_token, remaining_time)
        except jwt.JWTError:
            pass  # Token is already invalid, no need to blacklist

    if refresh_token:
        # Add refresh token to blacklist with its remaining expiration time
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")
            if exp:
                current_time = datetime.now(timezone.utc).timestamp()
                remaining_time = int(exp - current_time)
                if remaining_time > 0:
                    add_to_blacklist(refresh_token, remaining_time)
        except jwt.JWTError:
            pass  # Token is already invalid, no need to blacklist

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    create_user_request: CreateUserRequest, db: Session = Depends(get_db)
):

    check_if_user_exists(db, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


### ROUTE FOR LOGIN ###
class UserLogin(BaseModel):  # Create a Pydantic model for JSON request
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "yourpassword"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    id: int


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Login using email and password to get access token.
    """
    user = authenticate_user(email, password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user.email, user.id, user.role, timedelta(minutes=20)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "id": user.id
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token_get(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db),
):

    if refresh_token is None or not refresh_token.strip():
        raise HTTPException(status_code=401, detail="Refresh token missing or invalid")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")

        user = (
            db.query(OurUsers).filter(OurUsers.id == user_id).first()
        ) 
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            user_role=user.role,
            expires_delta=timedelta(minutes=20),
        )
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            samesite="lax",
            expires=20 * 60,
        )
        return {"message": "Refresh successful"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Refresh token expired"
        ) 
    except jwt.JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token"
        ) 


@router.post("/register/teacher", status_code=status.HTTP_201_CREATED)
async def register_teacher(
    create_user_request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    check_if_user_exists(db, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=UserRole.TEACHER.value,
        is_active=True,
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


@router.post("/create/admin", status_code=status.HTTP_201_CREATED)
async def register_admin(
    create_user_request: CreateUserRequest,
    db: Session = Depends(get_db),
):
    check_if_user_exists(db, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


@router.get("/users", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: Session = Depends(get_db),
):
    users = db.query(OurUsers).all()
    return users


@router.post("/reset-password")
async def request_password_reset(email: str, db: Session = Depends(get_db)):
    user = db.query(OurUsers).filter(OurUsers.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token, hashed_token = generate_password_reset_token()
    user.reset_token = hashed_token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    send_reset_password_email_task.delay(
        email, token
    )  # Used .delay() to send to Celery
    return {"message": "Password reset instructions sent to your email"}


@router.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    user = db.query(OurUsers).filter(OurUsers.reset_token == hashed_token).first()

    if not user or user.reset_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token is expired or wrong")

    user.hashed_password = bcrypt_context.hash(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    db.refresh(user)

    return {"message": "Password was changed!"}
