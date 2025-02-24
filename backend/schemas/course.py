from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.v1 import validator


class CourseBase(BaseModel):
    title: str
    description: str
    lessons_count: int
    lessons_duration: int ### in minutes for example ###
    files: List[str] ### for URLs to files(pdf)


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    lessons_count: int
    lessons_duration: int
    teacher_id: int

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



class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    lessons_count: Optional[int] = None
    lessons_duration: Optional[int] = None
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