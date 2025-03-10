from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import Course, OurUsers
from backend.models.assignment import Assignment
from backend.models.comment import Comment
from backend.oauth2 import get_current_user_jwt
from backend.schemas.assignment import AssignmentCreate, AssignmentWithCommentsResponse, AssignmentResponse

router = APIRouter(
    prefix="/courses/{course_id}/assignments",
    tags=["Assignments"],
)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AssignmentResponse)
async def create_assignment(
    course_id: int,
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),  # Authentication
):
    # Check if the user is a teacher or admin (add your authorization logic)
    if current_user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")

        # Check if the course exists AND belongs to the teacher (or if the user is an admin)
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter((Course.teacher_id == current_user["user_id"]) | (
                    current_user.get('role') == 'admin'))  # Admin override
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or you don't have permission.")


    new_assignment = Assignment(
        course_id=course_id,
        **assignment_data.dict()
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return new_assignment

@router.get("/{assignment_id}", response_model=AssignmentWithCommentsResponse)  # New response model
async def get_assignment(
    course_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    user: Optional[OurUsers] = db.query(OurUsers).filter(OurUsers.id == current_user['user_id']).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.course_id == course_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get comments for the assignment
    comments = db.query(Comment).filter(Comment.assignment_id == assignment_id).all()

    response_data = AssignmentWithCommentsResponse.from_orm(assignment)
    response_data.comments = comments
    return response_data

