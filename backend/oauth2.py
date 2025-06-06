import os
from datetime import timezone, datetime, timedelta

from fastapi import Depends, HTTPException, Cookie
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import OurUsers
from backend.services.token_blacklist import is_blacklisted

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 1))

### Check if user is in our DATABASE ###
def authenticate_user(email: EmailStr, password: str, db):
    user = db.query(OurUsers).filter(OurUsers.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    if not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    return user

### Create a JWT token for user ###
def create_access_token(email: EmailStr, user_id: int, user_role: str, expires_delta: timedelta) -> str:
    encode = {
        "sub": email,
        "id": user_id,
        "role": user_role,
        "token_type": "access_token",
    }
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int):
    encode = {"id": user_id, "token_type": "refresh_token"}
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

### Get current user from cookie ###
async def get_current_user_jwt(
    access_token: str = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    if not access_token:
        raise credentials_exception

    try:
        # Check if token is blacklisted
        if is_blacklisted(access_token):
            raise credentials_exception

        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
        user_role: str = payload.get("role")
        if user_role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(OurUsers).filter(OurUsers.email == email).first()
    if user is None:
        raise credentials_exception
        
    return {
        "user_id": user_id,
        "email": email,
        "role": user_role,
    }
