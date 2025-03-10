from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from backend.database import get_db
from backend.models import OurUsers, Course
from backend.models.enrollment import Enrollment
from backend.oauth2 import get_current_user_jwt
from backend.schemas.course import CourseResponse
from backend.schemas.user import UserLoginResponse

router = APIRouter(
    prefix='/student',
    tags=['student']
)


@router.put("/addToCourse/{course_id}")
async def addToCourse(course_id,
                      db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user_jwt)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This course does not exist")

    student: Optional[OurUsers] = db.query(OurUsers).filter(OurUsers.id == current_user['user_id']).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == student.id,
        Enrollment.course_id == course_id
    ).first()

    if existing_enrollment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already enrolled in this course")

    new_enrollment = Enrollment(user_id=student.id, course_id=course_id)
    db.add(new_enrollment)
    db.commit()

    return {"message": "User successfully enrolled in the course"}




@router.get("/my_students", response_model=List[UserLoginResponse], status_code=status.HTTP_200_OK)
async def get_my_students(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') != 'teacher':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Only teachers can access this endpoint.")

    teacher_id = current_user.get('user_id')
    if not teacher_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user token. Missing teacher ID.")


    #  Используем subquery для получения всех студентов всех курсов преподавателя
    students = db.query(OurUsers).join(Enrollment).join(Course).filter(Course.teacher_id == teacher_id).distinct().all()

    return students


@router.get("/my_courses", response_model=List[CourseResponse], status_code=status.HTTP_200_OK)
async def get_my_courses(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    student_id = current_user.get('user_id')
    if not student_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user token. Missing student ID.")

    student = db.query(OurUsers).filter(OurUsers.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    courses = db.query(Course).join(Enrollment).filter(Enrollment.user_id == student_id).all()

    return courses




@router.get("/getTeachersCourses/", response_model=List[CourseResponse], status_code=status.HTTP_200_OK)
async def get_course_by_id(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):


    if current_user.get('role') != 'teacher':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied. Only teachers can access this endpoint.")

    teacher_id = current_user.get('user_id')
    if not teacher_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user token. Missing teacher ID.")

    courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()

    return courses



@router.delete("/{student_id}/{course_id}")
async def delete_student(
            course_id: int,
            student_id: int,
            db: Session = Depends(get_db),
            current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This course does not exist")

    student = db.query(OurUsers).filter(OurUsers.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This student does not exist")

    enrollment = db.query(Enrollment).filter(Enrollment.course_id == course_id,
                                             Enrollment.user_id == student_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this course")

    db.delete(enrollment)
    db.commit()

    return {"message": "Student successfully removed from the course"}


