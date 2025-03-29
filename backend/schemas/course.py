from typing import List, Optional

from pydantic import ConfigDict, BaseModel
from pydantic.v1 import validator

from backend.schemas.user import TeacherOfCourse
from backend.schemas.section import SectionWithAssignments


class CourseBase(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    rating: Optional[int] = None
    lessons_count: int
    lessons_duration: int  ### in minutes for example ###
    files: List[str] = None  ### for URLs to files(pdf)


class CourseResponse(BaseModel):
    id: int
    teacher_id: int
    title: str
    description: str
    category: str
    rating: int
    ratings_count: int
    lessons_count: int
    lessons_duration: int
    files: Optional[List[str]] = None  ### Updated
    teacher: Optional[TeacherOfCourse] = None
    sections: Optional[List[SectionWithAssignments]] = None

    model_config = ConfigDict(from_attributes=True)

    @validator("files", pre=True)
    def validate_files(cls, files):
        if files is None:
            return []
        return files


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    lessons_count: Optional[int] = None
    lessons_duration: Optional[int] = None
    files: Optional[List[str]] = None


class CourseWithProgress(CourseResponse):
    completed_assignments: int = 0
    total_assignments: int = 0
    completion_percentage: float = 0.0


class CourseInfo(BaseModel):
    id: int
    title: str
    category: str
    rating: float
    teacher_id: int
    is_enrolled: bool = False
    completion_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)
