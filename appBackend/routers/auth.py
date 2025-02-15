from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from starlette import status

from appBackend.core.security import bcrypt_context
from appBackend.db.session   import get_db
from appBackend.models.ourusers import OurUsers
from appBackend.schemas.user import CreateUserRequest
router = APIRouter()




@router.post('/auth/', status_code=status.HTTP_201_CREATED)
async def create_user(
        create_user_request: CreateUserRequest,
        db: Session = Depends(get_db)):
    create_user_model = OurUsers(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return create_user_model
