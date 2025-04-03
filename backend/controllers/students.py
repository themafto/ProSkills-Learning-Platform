"""
Module for handling student-related operations including course enrollment and management.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from backend.database import get_db
from backend.models import Course, OurUsers
from backend.models.enrollment import Enrollment
from backend.oauth2 import get_current_user_jwt
from backend.schemas.course import CourseResponse
from backend.schemas.user import UserLoginResponse

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/enrollments/courses/{course_id}")
async def enroll_in_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
) -> dict:

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This course does not exist",
        )

    student: Optional[OurUsers] = (
        db.query(OurUsers).filter(OurUsers.id == current_user["user_id"]).first()
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == student.id, Enrollment.course_id == course_id)
        .first()
    )

    if existing_enrollment:
        return {"message": "User is already enrolled in this course"}

    new_enrollment = Enrollment(user_id=student.id, course_id=course_id)
    db.add(new_enrollment)
    db.commit()

    return {"message": "User successfully enrolled in the course"}


@router.get(
    "/teaching/courses/{course_id}/students",
    response_model=List[UserLoginResponse],
    status_code=status.HTTP_200_OK,
)
async def get_course_students(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all students enrolled in a specific course taught by the current teacher"""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only teachers can access this endpoint.",
        )

    teacher_id = current_user.get("user_id")
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user token. Missing teacher ID.",
        )

    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.teacher_id == teacher_id)
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or does not belong to the teacher.",
        )

    students = (
        db.query(OurUsers)
        .join(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .distinct()
        .all()
    )

    return students


@router.get("/enrollments/courses/{course_id}", status_code=status.HTTP_200_OK)
async def check_enrollment_status(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Check if the current user is enrolled in a specific course"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user token. Missing user ID.",
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )

    return {"is_enrolled": enrollment is not None}


@router.get(
    "/enrollments/courses",
    response_model=List[CourseResponse],
    status_code=status.HTTP_200_OK,
)
async def get_enrolled_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all courses the current student is enrolled in"""
    student_id = current_user.get("user_id")
    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user token. Missing student ID.",
        )

    student = db.query(OurUsers).filter(OurUsers.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    courses = (
        db.query(Course).join(Enrollment).filter(Enrollment.user_id == student_id).all()
    )

    return courses


@router.get(
    "/teaching/courses",
    response_model=List[CourseResponse],
    status_code=status.HTTP_200_OK,
)
async def get_teaching_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all courses the current teacher is teaching"""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only teachers can access this endpoint.",
        )

    teacher_id = current_user.get("user_id")
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user token. Missing teacher ID.",
        )

    courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()

    return courses


@router.delete("/enrollments/courses/{course_id}/students/{student_id}")
async def remove_student_enrollment(
    course_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Remove a student's enrollment from a course"""
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This course does not exist",
        )

    student = db.query(OurUsers).filter(OurUsers.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This student does not exist",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == student_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this course",
        )

    db.delete(enrollment)
    db.commit()

    return {"message": "Student successfully removed from the course"}
