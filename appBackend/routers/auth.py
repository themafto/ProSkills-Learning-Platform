from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from appBackend.db.session import SessionLocal
from appBackend.models.users import Users
from appBackend.schemas.user import CreateUserRequest
router = APIRouter()


def get_db():
    db = SessionLocal()
    try: yield db
    finally:
        db.close()


# не выводит ничего, а точнее пустой список
@router.get("/all_users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users

@router.post('/auth/')
async def create_user(create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=create_user_request.password,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True
    )
    return create_user_model