from typing import List, Optional

from pydantic import ConfigDict, BaseModel
from pydantic.v1 import validator

from backend.schemas.user import TeacherOfCourse


class CourseBase(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    rating: Optional[int] = None
    lessons_count: int
    lessons_duration: int ### in minutes for example ###
    files: List[str] = None ### for URLs to files(pdf)


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    lessons_count: int
    category: Optional[str] = None
    rating: Optional[int] = None
    lessons_duration: int
    files: Optional[List[str]]
    teacher: TeacherOfCourse



    model_config = ConfigDict(from_attributes=True)


class CourseCreate(CourseBase):
    files: Optional[List[str]] = None

    @validator('files', pre=True)
    def validate_files(cls, value):
        if value:
            for file_url in value:
                if not isinstance(file_url, str) or not (
                    file_url.lower().endswith('.pdf') or
                    file_url.startswith(('http://', 'https://'))):
                    raise ValueError('Invalid file format or URL')
        return value

class Course(CourseBase):
    id: int
    teacher_id: int

class CourseInfo(BaseModel):
    id: int
    title: str
    category: str
    rating: float
    teacher_id: int
    is_enrolled: bool

    model_config = ConfigDict(from_attributes=True)



class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    lessons_count: Optional[int] = None
    lessons_duration: Optional[int] = None
    category: Optional[str] = None
    files: Optional[List[str]] = None

    @validator('files', pre=True)
    def validate_files(cls, value):
        if value:
            for file_url in value:
                if not isinstance(file_url, str) or not (
                    file_url.lower().endswith('.pdf')
                    or file_url.startswith(('http://', 'https://'))
                ):
                    raise ValueError('Invalid file format or URL')
        return value