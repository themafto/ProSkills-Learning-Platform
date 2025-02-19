from datetime import timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.testing.pickleable import User, EmailUser

from starlette import status


from appBackend.core.security import bcrypt_context, authenticate_user, create_access_token, get_current_user_jwt
from appBackend.db.session   import get_db
from appBackend.models.ourusers import OurUsers
from appBackend.schemas.token import Token
from appBackend.schemas.user import CreateUserRequest, UserResponse
from appBackend.services.user_service import check_if_user_exists

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)



### ROUTE FOR REGISTRATION ###
@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(
        create_user_request: CreateUserRequest,
        db: Session = Depends(get_db)):

    check_if_user_exists(db, create_user_request.username, create_user_request.email)


    create_user_model = OurUsers(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role="student",
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


### ROUTE FOR LOGIN ###
class LoginRequest(BaseModel):
    email: str
    password: str
@router.post('/token', response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
        login_data: LoginRequest,
        db: Session = Depends(get_db)):
    user = authenticate_user(login_data.email, login_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.email, user.id, user.role, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'Bearer'}

@router.post('/register/teacher', status_code=status.HTTP_201_CREATED)
async def register_teacher(
        create_user_request: CreateUserRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    check_if_user_exists(db, create_user_request.username, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role="teacher",
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model

@router.post('/create/admin', status_code=status.HTTP_201_CREATED)
async def register_teacher(
        create_user_request: CreateUserRequest,
        db: Session = Depends(get_db),
):
    check_if_user_exists(db, create_user_request.username, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role="admin",
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model



@router.get("/users/", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
        db: Session = Depends(get_db),
):
    users = db.query(OurUsers).all()
    return users



