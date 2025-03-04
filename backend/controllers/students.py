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
from backend.schemas.user import UserOutPut

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

    student: Optional[OurUsers] = db.query(OurUsers).filter(OurUsers.id == current_user['id']).first()
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




@router.get("/getCoursesOnUser/{student_id}", response_model=List[CourseResponse], status_code=status.HTTP_200_OK)
async def get_course_by_id(
        student_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    student = db.query(OurUsers).filter(OurUsers.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This student does not exist")

    courses = db.query(Course).join(Course.students).filter(Enrollment.user_id == student_id).all()

    return courses

@router.get("/getStudentsOnCourse/{course_id}", response_model=List[UserOutPut], status_code=status.HTTP_200_OK)
async def get_students_on_course(
        course_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user_jwt)):

    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This course does not exist")

    students = db.query(OurUsers).join(OurUsers.courses).filter(Enrollment.course_id == course_id).all()

    return students

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


