from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from backend.schemas.comment import CommentResponse

class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    teacher_comments: Optional[str] = None
    order: Optional[int] = 0

class AssignmentCreate(AssignmentBase):
    course_id: int
    section_id: Optional[int] = None

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

class AssignmentResponse(AssignmentInDB):
    pass

class AssignmentWithCommentsResponse(AssignmentResponse):
    comments: List[CommentResponse]

class AssignmentWithProgressResponse(AssignmentResponse):
    is_completed: bool = False
    submission_file_key: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None