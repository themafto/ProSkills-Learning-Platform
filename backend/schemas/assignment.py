from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from fastapi import UploadFile

from backend.schemas.comment import CommentResponse


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    teacher_comments: Optional[str] = None
    order: Optional[int] = 0


class AssignmentCreate(AssignmentBase):
    section_id: Optional[int] = None


class AssignmentWithFileCreate(AssignmentCreate):
    file: Optional[UploadFile] = None


class AssignmentFile(BaseModel):
    key: str
    size: int
    last_modified: datetime
    filename: str


class AssignmentResponse(AssignmentBase):
    id: int
    course_id: int
    section_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    files: List[AssignmentFile] = []

    model_config = ConfigDict(from_attributes=True)


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    teacher_comments: Optional[str] = None
    section_id: Optional[int] = None
    order: Optional[int] = None


class AssignmentInDB(AssignmentBase):
    id: int
    course_id: int
    section_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentWithCommentsResponse(AssignmentResponse):
    comments: List[CommentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AssignmentWithProgressResponse(AssignmentResponse):
    is_completed: bool
    submission_file_key: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
