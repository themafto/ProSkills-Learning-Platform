from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SectionBase(BaseModel):
    title: str
    order: int
    course_id: int


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None


class SectionInDB(SectionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SectionResponse(SectionInDB):
    pass


class SectionWithAssignments(SectionInDB):
    assignments: List["AssignmentInDB"] = []

    model_config = ConfigDict(from_attributes=True)


# This will be imported in assignment.py
from backend.schemas.assignment import AssignmentInDB

SectionWithAssignments.model_rebuild()
