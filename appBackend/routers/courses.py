from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from appBackend.core.security import get_current_user_jwt
from appBackend.db.session import get_db
from appBackend.schemas.course import Course, CourseCreate

router = APIRouter(
    prefix='/courses',
    tags=['courses']
)



@router.post("/create_course",response_model=Course, status_code=status.HTTP_201_CREATED)
async def create_course(
        create_course_request: CourseCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') != 'teacher':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    course = Course(
        **create_course_request.model_dump(),
        teacher_id = current_user.get("user_id") ### get an id of teacher
    )

    db.add(course)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating course: {e}")
    db.refresh(course)
    return course

@router.get("/courses",response_model=List[Course])
async def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()