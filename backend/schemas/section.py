from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# Import needed for forward reference
from backend.schemas.assignment import AssignmentInDB


class SectionBase(BaseModel):
    title: str
    order: int


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


SectionWithAssignments.model_rebuild()
