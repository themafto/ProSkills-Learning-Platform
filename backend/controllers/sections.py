from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.getdb import get_db
from backend.models import Course, Section
from backend.oauth2 import get_current_user_jwt
from backend.schemas.section import (
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SectionWithAssignments,
)

router = APIRouter(prefix="/sections", tags=["sections"])


@router.post("", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    course_id: int,
    section_data: SectionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Create a new section for a course"""
    # Check if user is teacher or admin
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create sections",
        )

    # Check if course exists and user is the teacher of the course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Check if user is the teacher of the course
    if current_user.get("role") != "admin" and course.teacher_id != current_user.get(
        "user_id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create sections for this course",
        )

    # Create the section using course_id from URL
    section = Section(**section_data.model_dump(), course_id=course_id)

    try:
        db.add(section)
        db.commit()
        db.refresh(section)
        return section
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating section: {str(e)}",
        )


@router.get("/{section_id}", response_model=SectionWithAssignments)
async def get_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get a section by ID with its assignments"""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section not found"
        )

    # Get the associated course to check permissions
    course = db.query(Course).filter(Course.id == section.course_id).first()

    # Check if user has permission to view (enrolled in course, teacher, or admin)
    is_teacher = course.teacher_id == current_user.get("user_id")
    is_admin = current_user.get("role") == "admin"

    if not (is_teacher or is_admin):
        # Check if student is enrolled in the course
        is_enrolled = False
        for student in course.students:
            if student.id == current_user.get("user_id"):
                is_enrolled = True
                break

        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this section",
            )

    return section


@router.get("/course/{course_id}", response_model=List[SectionWithAssignments])
async def get_course_sections(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Get all sections for a course"""
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Check if user has permission to view (enrolled in course, teacher, or admin)
    is_teacher = course.teacher_id == current_user.get("user_id")
    is_admin = current_user.get("role") == "admin"

    if not (is_teacher or is_admin):
        # Check if student is enrolled in the course
        is_enrolled = False
        for student in course.students:
            if student.id == current_user.get("user_id"):
                is_enrolled = True
                break

        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view sections for this course",
            )

    # Get all sections for the course
    sections = (
        db.query(Section)
        .filter(Section.course_id == course_id)
        .order_by(Section.order)
        .all()
    )
    return sections


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    section_data: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Update a section"""
    # Check if section exists
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section not found"
        )

    # Get the associated course
    course = db.query(Course).filter(Course.id == section.course_id).first()

    if current_user.get("role") != "admin" and course.teacher_id != current_user.get(
        "user_id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this section",
        )

    # Update the section
    update_data = section_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(section, key, value)

    try:
        db.commit()
        db.refresh(section)
        return section
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating section: {str(e)}",
        )


@router.delete("/{section_id}", status_code=status.HTTP_200_OK)
async def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_jwt),
):
    """Delete a section"""
    # Check if section exists
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section not found"
        )

    # Get the associated course
    course = db.query(Course).filter(Course.id == section.course_id).first()

    # Check if user is the teacher of the course or admin
    if current_user.get("role") != "admin" and course.teacher_id != current_user.get(
        "user_id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this section",
        )

    try:
        db.delete(section)
        db.commit()
        return {"message": "Section deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting section: {str(e)}",
        )
