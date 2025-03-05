from typing import List

import sqlalchemy
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session, joinedload

from starlette import status


from backend.dependencies.getdb import get_db
from backend.models import Course
from backend.oauth2 import get_current_user_jwt
from backend.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseInfo
from backend.schemas.user import UserResponse, TeacherOfCourse

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

    course_dict = course.to_dict()
    course_dict['teacher'] = TeacherOfCourse.model_validate(course.teacher.to_dict())
    return CourseResponse.model_validate(course_dict)

@router.get("/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def get_course_by_id(course_id: int, db: Session = Depends(get_db)):

    # Use joinedload specifically for the teacher relationship
    course = db.query(Course).options(joinedload(Course.teacher)).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course

@router.put("/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def update_course(
        course_id: int,
        update_course_request: CourseUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    ###  Authorization by ownership ###
    if course.teacher_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = update_course_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)

    try:
        db.commit()
        db.refresh(course)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating course: {e}")
    return course

@router.get("/", response_model=List[CourseInfo])
async def get_all_courses(db: Session = Depends(get_db)):
    try:
        courses = db.query(Course).all()
        return courses  # objects of SQLAlchemy
    except Exception as e:
        print(e)  # or logging.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def delete_course(
        course_id: int,
        current_user: dict = Depends(get_current_user_jwt),
        db: Session = Depends(get_db)):

    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    course = db.query(Course).filter(Course.id == course_id).delete()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course

