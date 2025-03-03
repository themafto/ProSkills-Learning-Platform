from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Cookie
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from starlette import status
from fastapi.responses import JSONResponse
from backend.dependencies.getdb import get_db
from backend.models.ourusers import OurUsers
from backend.oauth2 import bcrypt_context, authenticate_user, create_access_token, get_current_user_jwt, \
    create_refresh_token, SECRET_KEY, ALGORITHM
from backend.roles import UserRole
from backend.schemas.token import Token
from backend.schemas.user import CreateUserRequest, UserResponse
from backend.services.user_service import check_if_user_exists


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
        role=UserRole.STUDENT.value,
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model


### ROUTE FOR LOGIN ###
class UserLogin(BaseModel):  # Create a Pydantic model for JSON request
    email: str
    password: str
@router.post('/token', response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
        login_data: UserLogin,
        db: Session = Depends(get_db)):


    user = authenticate_user(login_data.email, login_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.email, user.id, user.role, timedelta(minutes=20))
    refresh_token = create_refresh_token(user.id)

    response = JSONResponse(content={"access_token": access_token,"refresh_token": refresh_token, "token_type": "Bearer"})
    return response



@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token_get(
        refresh_token: str,
        db: Session = Depends(get_db)):

    if refresh_token is None or not refresh_token.strip():  # Also check for empty strings
        raise HTTPException(status_code=401, detail="Refresh token missing or invalid")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id:int  = payload.get("id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid refresh token")

    try:
        user_id_int = int(user_id)  # Convert the incoming user_id string to an integer
        user_db = db.query(OurUsers).filter(OurUsers.id == user_id_int).first()  # Query again using the integer

        if not user_db:  # recheck since the id may not have been a proper integer corresponding to a real record
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        new_access_token = create_access_token(  # Presumed function not included in question.
            email=str(user_db.email),
            user_id=user_id_int,
            user_role=str(user_db.role),
            expires_delta=timedelta(minutes=20)
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Invalid user ID format")  # More appropriate
    except Exception as e:
        # Log the error for debugging.!!!!! Do not expose it in production without sanitation. !!!!
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error")  # generic




@router.post('/register/teacher', status_code=status.HTTP_201_CREATED)
async def register_teacher(
        create_user_request: CreateUserRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):
    if current_user.get('role') != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    check_if_user_exists(db, create_user_request.username, create_user_request.email)

    create_user_model = OurUsers(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=UserRole.TEACHER.value,
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model

@router.post('/create/admin', status_code=status.HTTP_201_CREATED, response_model=None)
async def register_admin(
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
        role=UserRole.ADMIN.value,
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



