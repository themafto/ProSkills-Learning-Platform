from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, validator


class AssignmentProgressBase(BaseModel):
    student_id: int
    assignment_id: int
    course_id: Optional[int] = None
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
    completed_assignments: int = Field(default=0, ge=0)
    total_assignments: int = Field(default=0, ge=0)
    last_activity: Optional[datetime] = None


class CourseProgressCreate(CourseProgressBase):
    pass


class CourseProgressUpdate(BaseModel):
    completed_assignments: Optional[int] = Field(default=None, ge=0)
    total_assignments: Optional[int] = Field(default=None, ge=0)
    last_activity: Optional[datetime] = None


class CourseProgressInDB(CourseProgressBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(CourseProgressInDB):
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    @validator('completion_percentage', pre=True)
    def validate_completion_percentage(cls, v):
        if v is None:
            return 0.0
        try:
            value = float(v)
            return round(max(0.0, min(100.0, value)), 2)
        except (TypeError, ValueError):
            return 0.0

    model_config = ConfigDict(from_attributes=True)
