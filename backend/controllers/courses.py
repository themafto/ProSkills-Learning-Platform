from typing import List

import sqlalchemy
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session, joinedload

from starlette import status


from backend.dependencies.getdb import get_db
from backend.models import Course, OurUsers
from backend.models.enrollment import Enrollment
from backend.models.rating import Rating
from backend.oauth2 import get_current_user_jwt
from backend.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseInfo,
)
from backend.schemas.rating import RatingResponse, RatingCreate
from backend.schemas.user import UserResponse, TeacherOfCourse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post(
    "/create_course", response_model=CourseResponse, status_code=status.HTTP_201_CREATED
)
async def create_course(
    create_course_request: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    course = Course(
        **create_course_request.model_dump(),
        teacher_id=current_user.get("user_id"),  ### get an id of teacher
    )

    db.add(course)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating course: {e}")
    db.refresh(course)

    course_dict = course.to_dict()
    course_dict["teacher"] = TeacherOfCourse.model_validate(course.teacher.to_dict())
    return CourseResponse.model_validate(course_dict)


@router.get(
    "/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK
)
async def get_course_by_id(course_id: int, db: Session = Depends(get_db)):

    # Use joinedload specifically for the teacher relationship
    course = (
        db.query(Course)
        .options(joinedload(Course.teacher))
        .filter(Course.id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    course_dict = course.to_dict()
    course_dict["teacher"] = TeacherOfCourse.model_validate(course.teacher.to_dict())
    return CourseResponse.model_validate(course_dict)


@router.put(
    "/{course_id}", response_model=CourseResponse, status_code=status.HTTP_200_OK
)
async def update_course(
    course_id: int,
    update_course_request: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):

    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating course: {e}",
        )
    return course


@router.get("", response_model=List[CourseInfo])
async def get_all_courses(db: Session = Depends(get_db)):
    try:
        courses = db.query(Course).options(joinedload(Course.teacher)).all()

        courses_info = []
        for course in courses:
            courses_info.append(
                CourseInfo(
                    id=course.id,
                    title=course.title,
                    category=course.category,
                    rating=course.rating,
                    teacher_id=course.teacher_id,
                )
            )
        return courses_info

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
async def delete_course(
    course_id: int,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):

    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    course = db.query(Course).filter(Course.id == course_id)
    if (
        not db.query(Course).filter(Course.id == course_id).first()
    ):  # Check if the course exists
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    course.delete()
    db.commit()

    return {"message": "Course deleted successfully"}


@router.post("/{course_id}/rate", response_model=RatingResponse, status_code=201)
async def rate_course(
    course_id: int,
    rating_data: RatingCreate,
    current_user: dict = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing_rating = (
        db.query(Rating)
        .filter(Rating.user_id == current_user["user_id"], Rating.course_id == course_id)
        .first()
    )

    if existing_rating:
        raise HTTPException(status_code=400, detail="User already rated this course")

    new_rating = Rating(
        user_id=current_user["user_id"], course_id=course_id, rating=rating_data.rating
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)

    # Update course rating
    all_ratings = db.query(Rating).filter(Rating.course_id == course_id).all()
    total_rating = sum(r.rating for r in all_ratings)
    course.ratings_count = len(all_ratings)
    course.rating = (
        total_rating / course.ratings_count if course.ratings_count else 0.0
    )  # Calculate the new average
    db.commit()

    return new_rating
