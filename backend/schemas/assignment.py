from typing import Optional, List


from pydantic import BaseModel
from datetime import datetime

from backend.schemas.comment import CommentResponse



class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    teacher_comments: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AssignmentWithCommentsResponse(AssignmentResponse):
    comments: List[CommentResponse]