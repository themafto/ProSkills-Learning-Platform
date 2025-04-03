"""
Module for handling course and assignment progress tracking.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import Assignment, Course, AssignmentProgress, CourseProgress
from backend.models.enrollment import Enrollment
from backend.oauth2 import get_current_user_jwt
from backend.schemas.progress import (
    AssignmentProgressCreate,
    AssignmentProgressResponse,
    AssignmentProgressUpdate,
    CourseProgressResponse,
)
from backend.schemas.assignment import AssignmentWithProgressResponse

router = APIRouter(prefix="/progress", tags=["progress"])


def check_enrollment(db: Session, student_id: int, course_id: int) -> bool:
    """
    Check if a student is enrolled in a course.

    Args:
        db: Database session
        student_id: ID of the student
        course_id: ID of the course

    Returns:
        bool: True if student is enrolled, False otherwise
    """
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == student_id, Enrollment.course_id == course_id)
        .first()
        is not None
    )


# Helper function to ensure course progress record exists
def get_or_create_course_progress(db: Session, student_id: int, course_id: int):
    progress = (
        db.query(CourseProgress)
        .filter(
            CourseProgress.student_id == student_id,
            CourseProgress.course_id == course_id,
        )
        .first()
    )

    if not progress:
        # Get total assignments for this course
        total_assignments = (
            db.query(Assignment).filter(Assignment.course_id == course_id).count()
        )

        # Create new progress record
        progress = CourseProgress(
            student_id=student_id,
            course_id=course_id,
            total_assignments=total_assignments,
            completed_assignments=0,
            last_activity=datetime.now(),
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return progress


# Helper function to update course progress after assignment completion
def update_course_progress(db: Session, student_id: int, course_id: int):
    course_progress = (
        db.query(CourseProgress)
        .filter(
            CourseProgress.student_id == student_id,
            CourseProgress.course_id == course_id,
        )
        .first()
    )

    if course_progress:
        # Count completed assignments
        completed_count = (
            db.query(AssignmentProgress)
            .join(Assignment, Assignment.id == AssignmentProgress.assignment_id)
            .filter(
                Assignment.course_id == course_id,
                AssignmentProgress.student_id == student_id,
                AssignmentProgress.is_completed == True,
            )
            .count()
        )

        # Update course progress
        course_progress.completed_assignments = completed_count
        course_progress.last_activity = datetime.now()
        db.commit()
        db.refresh(course_progress)

    return course_progress


@router.post("/assignments/{assignment_id}", response_model=AssignmentProgressResponse)
async def create_or_update_assignment_progress(
    assignment_id: int,
    progress_data: AssignmentProgressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Create or update progress for an assignment"""
    user_id = current_user.get("user_id")

    # Students can only update their own progress
    if progress_data.student_id != user_id and current_user.get("role") not in [
        "teacher",
        "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update progress for other students",
        )

    # Check if assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if student is enrolled in the course
    if not check_enrollment(db, progress_data.student_id, assignment.course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not enrolled in this course",
        )

    # Check if progress record already exists
    progress = (
        db.query(AssignmentProgress)
        .filter(
            AssignmentProgress.student_id == progress_data.student_id,
            AssignmentProgress.assignment_id == assignment_id,
        )
        .first()
    )

    if progress:
        # Update existing progress
        update_data = progress_data.model_dump(exclude_unset=True)
        update_data.pop("student_id", None)  # Cannot change student ID
        update_data.pop("assignment_id", None)  # Cannot change assignment ID

        for key, value in update_data.items():
            setattr(progress, key, value)

        # If marking as complete, set completed_at time
        if progress_data.is_completed and not progress.completed_at:
            progress.completed_at = datetime.now()

        db.commit()
        db.refresh(progress)
    else:
        # Create new progress record
        progress = AssignmentProgress(
            student_id=progress_data.student_id,
            assignment_id=assignment_id,
            **progress_data.model_dump(exclude={"student_id", "assignment_id"})
        )

        # If marked as complete, set completed_at time
        if progress_data.is_completed:
            progress.completed_at = datetime.now()

        # If has submission, set submitted_at time
        if progress_data.submission_file_key:
            progress.submitted_at = datetime.now()

        db.add(progress)
        db.commit()
        db.refresh(progress)

    # Update course progress
    update_course_progress(db, progress_data.student_id, assignment.course_id)

    return progress


@router.get(
    "/assignments/{assignment_id}/student/{student_id}",
    response_model=AssignmentProgressResponse,
)
async def get_assignment_progress(
    assignment_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get progress for an assignment"""
    user_id = current_user.get("user_id")

    # Students can only view their own progress
    if student_id != user_id and current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view progress for other students",
        )

    # Check if assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Get progress
    progress = get_assignment_progress(db, student_id, assignment_id)

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found"
        )

    return progress


@router.put("/assignments/{assignment_id}", response_model=AssignmentProgressResponse)
async def update_assignment_progress(
    assignment_id: int,
    progress_data: AssignmentProgressUpdate,
    student_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Update progress for an assignment"""
    user_id = current_user.get("user_id")

    # If student_id not provided, use current user's ID
    if not student_id:
        student_id = user_id

    # Students can only update their own progress
    if student_id != user_id and current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update progress for other students",
        )

    # Check if assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if student is enrolled in the course
    if not check_enrollment(db, student_id, assignment.course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not enrolled in this course",
        )

    # Get progress
    progress = get_assignment_progress(db, student_id, assignment_id)

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found"
        )

    # Update progress
    update_data = progress_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(progress, key, value)

    # If marking as complete, set completed_at time
    if progress_data.is_completed and not progress.completed_at:
        progress.completed_at = datetime.now()

    # If has new submission, update submitted_at time
    if (
        progress_data.submission_file_key
        and progress_data.submission_file_key != progress.submission_file_key
    ):
        progress.submitted_at = datetime.now()

    db.commit()
    db.refresh(progress)

    # Update course progress
    update_course_progress(db, student_id, assignment.course_id)

    return progress


@router.get(
    "/courses/{course_id}/student/{student_id}", response_model=CourseProgressResponse
)
async def get_course_progress(
    course_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get progress for a course"""
    user_id = current_user.get("user_id")

    # Students can only view their own progress
    if student_id != user_id and current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view progress for other students",
        )

    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Check if student is enrolled in the course
    if not check_enrollment(db, student_id, course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not enrolled in this course",
        )

    # Get or create progress
    progress = get_or_create_course_progress(db, student_id, course_id)

    return progress


@router.get(
    "/courses/{course_id}/assignments",
    response_model=List[AssignmentWithProgressResponse],
)
async def get_assignments_with_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all assignments for a course with progress for the current user"""
    user_id = current_user.get("user_id")

    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Check if user is teacher of the course or enrolled
    is_teacher = course.teacher_id == user_id
    is_admin = current_user.get("role") == "admin"

    if not (is_teacher or is_admin):
        # Check if student is enrolled
        if not check_enrollment(db, user_id, course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this course",
            )

    # Get all assignments for the course
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()

    # Get progress for each assignment
    result = []
    for assignment in assignments:
        progress = get_assignment_progress(db, user_id, assignment.id)

        assignment_dict = assignment.to_dict()

        if progress:
            assignment_dict.update(
                {
                    "is_completed": progress.is_completed,
                    "submission_file_key": progress.submission_file_key,
                    "score": progress.score,
                    "feedback": progress.feedback,
                }
            )
        else:
            assignment_dict.update(
                {
                    "is_completed": False,
                    "submission_file_key": None,
                    "score": None,
                    "feedback": None,
                }
            )

        result.append(AssignmentWithProgressResponse(**assignment_dict))

    return result


@router.post(
    "/mark-assignment-complete/{assignment_id}",
    response_model=AssignmentProgressResponse,
)
async def mark_assignment_complete(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Mark an assignment as complete for the current user"""
    user_id = current_user.get("user_id")

    # Check if assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if student is enrolled in the course
    if not check_enrollment(db, user_id, assignment.course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course",
        )

    # Get progress or create new
    progress = get_assignment_progress(db, user_id, assignment_id)

    if not progress:
        progress = AssignmentProgress(
            student_id=user_id,
            assignment_id=assignment_id,
            is_completed=True,
            completed_at=datetime.now(),
        )
        db.add(progress)
    else:
        progress.is_completed = True
        if not progress.completed_at:
            progress.completed_at = datetime.now()

    db.commit()
    db.refresh(progress)

    # Update course progress
    update_course_progress(db, user_id, assignment.course_id)

    return progress


def get_assignment_progress(db: Session, student_id: int, assignment_id: int) -> Optional[AssignmentProgress]:
    """
    Get progress for a specific assignment.

    Args:
        db: Database session
        student_id: ID of the student
        assignment_id: ID of the assignment

    Returns:
        Optional[AssignmentProgress]: Progress record if found, None otherwise
    """
    return db.query(AssignmentProgress).filter(
        AssignmentProgress.student_id == student_id,
        AssignmentProgress.assignment_id == assignment_id,
        AssignmentProgress.is_completed is True  # Fixed comparison
    ).first()
