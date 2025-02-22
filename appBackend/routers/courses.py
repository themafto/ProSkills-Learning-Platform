from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm.sync import update
from starlette import status

from appBackend.core.security import get_current_user_jwt
from appBackend.db.session import get_db
from appBackend.models import Course
from appBackend.schemas.course import CourseCreate, CourseBase, CourseUpdate, CourseResponse

router = APIRouter(
    prefix='/courses',
    tags=['courses']
)



@router.post("/create_course", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
        create_course_request: CourseCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):
    if current_user.get('role') not in ['teacher', 'admin']:
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

    return CourseResponse.model_validate(course.to_dict())

@router.get("/courses/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def get_courses(db: Session = Depends(get_db)):
    courses = db.query(CourseBase).all()
    return courses

@router.put("/courses/update", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def update_course(
        course_id: int,
        update_course_request: CourseUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') != 'teacher':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    ###  Authorization by ownership ###
    if course.teacher_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Not authorized to update this course")

    update_data = update_course_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)

    try:
        db.commit()
        db.refresh(course)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating course: {e}")

    return course.model_dump()



