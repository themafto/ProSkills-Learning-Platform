import os
from datetime import timezone, datetime, timedelta

from fastapi import Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import OurUsers

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 1))

### Check if user is in our DATABASE ###
def authenticate_user(email: str, password: str, db):
    user = db.query(OurUsers).filter(OurUsers.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

### Create a JWT token for user ###
def create_access_token(email: str, user_id: int, user_role: str, expires_delta: timedelta) -> object:
    encode = {'sub': email, 'id': user_id, 'role': user_role, 'token_type': 'access_token'}
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token( user_id: int):
    encode = {'id': user_id, 'token_type': 'refresh_token'}
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

### Checking if the JWT Token of our user is correct ###
async def get_current_user_jwt(db: Session = Depends(get_db),
                               access_token: str = Cookie(None, alias="access_token")):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Access token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")

        user = db.query(OurUsers).filter(OurUsers.id == user_id, OurUsers.email == email).first()
        if user is None or user.role != user_role:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"email": email, "user_id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
