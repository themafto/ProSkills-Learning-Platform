from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AssignmentProgressBase(BaseModel):
    student_id: int
    assignment_id: int
    is_completed: bool = False
    submission_file_key: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    completed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None


class AssignmentProgressCreate(AssignmentProgressBase):
    pass


class AssignmentProgressUpdate(BaseModel):
    is_completed: Optional[bool] = None
    submission_file_key: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    completed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None


class AssignmentProgressInDB(AssignmentProgressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AssignmentProgressResponse(AssignmentProgressInDB):
    pass


class CourseProgressBase(BaseModel):
    student_id: int
    course_id: int
    completed_assignments: int = 0
    total_assignments: int = 0
    last_activity: Optional[datetime] = None


class CourseProgressCreate(CourseProgressBase):
    pass


class CourseProgressUpdate(BaseModel):
    completed_assignments: Optional[int] = None
    total_assignments: Optional[int] = None
    last_activity: Optional[datetime] = None


class CourseProgressInDB(CourseProgressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(CourseProgressInDB):
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
