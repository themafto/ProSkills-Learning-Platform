from datetime import timedelta, datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette import status

from appBackend.db.session import get_db
from appBackend.models.ourusers import OurUsers

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


SECRET_KEY = 'a7c6df360291729a64a04dee33078576a2008b25c7e3e7f8cf3ee0a5a085616c'  # for testing #
ALGORITHM = 'HS256'


### Check if user is in our DATABASE ###
def authenticate_user(email: str, password: str, db):
    user = db.query(OurUsers).filter(OurUsers.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


### Create a JWT token for user ###
def create_access_token(email: str, user_id: int, user_role: str, expires_delta: timedelta):
    encode = {'sub': email, 'id': user_id, 'role': user_role}
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


### Checking if the JWT Token of our user is correct ###
async def get_current_user_jwt(db: Session = Depends(get_db), token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload['sub']
        user_id: int = payload['id']
        user_role: str = payload['role']
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Incorrect username or password')

        ### Finding user in DB (for security) ###
        user = db.query(OurUsers).filter(OurUsers.id == user_id,OurUsers.email == email).first()  # check id and username #
        if user is None or user.role != user_role:  # Checking role #
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

        return {'username': email, 'user_id': user_id, 'role': user_role}
    except JWTError:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='Incorrect email or password')


