from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import Course, OurUsers, Section, AssignmentProgress
from backend.models.assignment import Assignment
from backend.models.comment import Comment
from backend.oauth2 import get_current_user_jwt
from backend.schemas.assignment import (
    AssignmentCreate,
    AssignmentWithCommentsResponse,
    AssignmentResponse,
    AssignmentUpdate,
    AssignmentWithProgressResponse,
    AssignmentWithFileCreate,
)
from backend.schemas.file import FileUploadResponse
from backend.controllers.filesForCourse import validate_file, s3, BUCKET_NAME
import uuid
import base64

router = APIRouter(
    prefix="/courses/{course_id}/assignments",
    tags=["Assignments"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AssignmentResponse)
async def create_assignment(
    course_id: int,
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    # Check if the user is a teacher or admin
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if the course exists AND belongs to the teacher (or if the user is an admin)
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(
            (Course.teacher_id == current_user["user_id"])
            | (current_user.get("role") == "admin")
        )
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=404, detail="Course not found or you don't have permission."
        )

    # Validate section_id if provided
    if assignment_data.section_id:
        section = (
            db.query(Section)
            .filter(
                Section.id == assignment_data.section_id, Section.course_id == course_id
            )
            .first()
        )
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found or does not belong to this course",
            )

    # Create new assignment using course_id from URL
    new_assignment = Assignment(
        **assignment_data.model_dump(),
        course_id=course_id  # Use course_id from URL parameter
    )

    db.add(new_assignment)
    try:
        db.commit()
        db.refresh(new_assignment)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating assignment: {str(e)}"
        )

    # Update total assignments count in all student progress records
    course_students = course.students
    for student in course_students:
        progress = (
            db.query(AssignmentProgress)
            .filter(
                AssignmentProgress.student_id == student.id,
                AssignmentProgress.course_id == course_id,
            )
            .first()
        )

        if progress:
            progress.total_assignments += 1
            db.commit()

    return new_assignment


@router.post("/with-file", status_code=status.HTTP_201_CREATED, response_model=AssignmentResponse)
async def create_assignment_with_file(
    course_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date: Optional[datetime] = Form(None),
    teacher_comments: Optional[str] = Form(None),
    section_id: Optional[int] = Form(None),
    order: Optional[int] = Form(0),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """
    Create a new assignment with an optional file upload in a single request.
    """
    # Check if the user is a teacher or admin
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if the course exists AND belongs to the teacher (or if the user is an admin)
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(
            (Course.teacher_id == current_user["user_id"])
            | (current_user.get("role") == "admin")
        )
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=404, detail="Course not found or you don't have permission."
        )

    # Convert section_id=0 to None
    if section_id == 0:
        section_id = None

    # Validate section_id if provided
    if section_id:
        section = (
            db.query(Section)
            .filter(
                Section.id == section_id, Section.course_id == course_id
            )
            .first()
        )
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found or does not belong to this course",
            )

    # Create new assignment
    new_assignment = Assignment(
        title=title,
        description=description,
        due_date=due_date,
        teacher_comments=teacher_comments,
        section_id=section_id,  # Now section_id will be None if it was 0
        order=order,
        course_id=course_id
    )

    db.add(new_assignment)
    try:
        db.commit()
        db.refresh(new_assignment)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating assignment: {str(e)}"
        )

    # Handle file upload if provided
    if file:
        try:
            # Validate file
            file_content = await validate_file(file)

            # Create a structured key for assignments with uniqueness
            key = f"assignments/{new_assignment.id}/task/{uuid.uuid4().hex}_{file.filename}"

            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=file_content,
                ContentType=file.content_type,
            )

        except Exception as e:
            print(f"Error uploading file: {str(e)}")

    # Update total assignments count in all student progress records
    course_students = course.students
    for student in course_students:
        progress = (
            db.query(AssignmentProgress)
            .filter(
                AssignmentProgress.student_id == student.id,
                AssignmentProgress.course_id == course_id,
            )
            .first()
        )

        if progress:
            progress.total_assignments += 1
            db.commit()

    return new_assignment


@router.get("/{assignment_id}", response_model=AssignmentWithCommentsResponse)
async def get_assignment(
    course_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    user: Optional[OurUsers] = (
        db.query(OurUsers).filter(OurUsers.id == current_user["user_id"]).first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.course_id == course_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get comments for the assignment
    comments = db.query(Comment).filter(Comment.assignment_id == assignment_id).all()

    # Convert to response model
    assignment_dict = assignment.to_dict()
    assignment_dict["comments"] = comments

    return AssignmentWithCommentsResponse(**assignment_dict)


@router.get(
    "/{assignment_id}/progress", response_model=AssignmentWithProgressResponse
)
async def get_assignment_with_progress(
    course_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get assignment with the current user's progress"""
    user_id = current_user.get("user_id")

    # Check if assignment exists and belongs to the course
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.course_id == course_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get progress for this assignment
    progress = (
        db.query(AssignmentProgress)
        .filter(
            AssignmentProgress.assignment_id == assignment_id,
            AssignmentProgress.student_id == user_id,
        )
        .first()
    )

    # Convert to response model
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

    return AssignmentWithProgressResponse(**assignment_dict)


@router.get("", response_model=List[AssignmentResponse])
async def get_course_assignments(
    course_id: int,
    section_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all assignments for a course, optionally filtered by section"""
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user has permission to view (teacher, admin, or enrolled student)
    user_id = current_user.get("user_id")
    is_teacher = course.teacher_id == user_id
    is_admin = current_user.get("role") == "admin"

    if not (is_teacher or is_admin):
        # Check if student is enrolled
        is_enrolled = False
        for student in course.students:
            if student.id == user_id:
                is_enrolled = True
                break

        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view assignments for this course",
            )

    # Build query
    query = db.query(Assignment).filter(Assignment.course_id == course_id)

    # Filter by section if provided
    if section_id is not None:
        section = (
            db.query(Section)
            .filter(Section.id == section_id, Section.course_id == course_id)
            .first()
        )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found or does not belong to this course",
            )

        query = query.filter(Assignment.section_id == section_id)

    # Order by section and then by order within section
    assignments = query.order_by(Assignment.section_id, Assignment.order).all()

    # Get file information for each assignment
    result = []
    for assignment in assignments:
        assignment_dict = assignment.to_dict()
        
        # Get files for this assignment from S3
        try:
            prefix = f"assignments/{assignment.id}/task/"
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
            
            if "Contents" in response:
                files = []
                for item in response["Contents"]:
                    # Get the file content from S3
                    file_response = s3.get_object(Bucket=BUCKET_NAME, Key=item["Key"])
                    file_content = file_response["Body"].read()
                    
                    # Convert to base64
                    file_base64 = base64.b64encode(file_content).decode('utf-8')
                    
                    files.append({
                        "key": item["Key"],
                        "size": item["Size"],
                        "last_modified": item["LastModified"],
                        "filename": item["Key"].split("/")[-1],
                        "content": file_base64,
                        "content_type": file_response.get("ContentType", "application/octet-stream")
                    })
                assignment_dict["files"] = files
            else:
                assignment_dict["files"] = []
        except Exception as e:
            print(f"Error getting files for assignment {assignment.id}: {str(e)}")
            assignment_dict["files"] = []

        result.append(AssignmentResponse(**assignment_dict))

    return result


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    course_id: int,
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Update an assignment"""
    # Check if the user is a teacher or admin
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if assignment exists and belongs to the course
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.course_id == course_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check if user is the teacher of the course or admin
    course = db.query(Course).filter(Course.id == course_id).first()
    if current_user.get("role") != "admin" and course.teacher_id != current_user.get(
        "user_id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update assignments for this course",
        )

    # Validate section_id if being updated
    if assignment_data.section_id is not None:
        if assignment_data.section_id > 0:  # Allow setting to None by using 0
            section = (
                db.query(Section)
                .filter(
                    Section.id == assignment_data.section_id,
                    Section.course_id == course_id,
                )
                .first()
            )
            if not section:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Section not found or does not belong to this course",
                )
        else:
            assignment_data.section_id = None  # Convert 0 to None

    # Update assignment
    update_data = assignment_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
async def delete_assignment(
    course_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Delete an assignment"""
    # Check if the user is a teacher or admin
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if assignment exists and belongs to the course
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.course_id == course_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check if user is the teacher of the course or admin
    course = db.query(Course).filter(Course.id == course_id).first()
    if current_user.get("role") != "admin" and course.teacher_id != current_user.get(
        "user_id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete assignments for this course",
        )

    # Delete assignment
    db.delete(assignment)
    db.commit()

    # Update total assignments count in all student progress records
    course_students = course.students
    for student in course_students:
        progress = (
            db.query(AssignmentProgress)
            .filter(
                AssignmentProgress.student_id == student.id,
                AssignmentProgress.course_id == course_id,
            )
            .first()
        )

        if progress and progress.total_assignments > 0:
            progress.total_assignments -= 1
            db.commit()

    return {"message": "Assignment deleted successfully"}
