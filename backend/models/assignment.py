from datetime import datetime
from typing import Optional

from backend.models.basemodel import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey


class Assignment(BaseModel):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    section_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sections.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    teacher_comments: Mapped[str] = mapped_column(String, default="")
    order: Mapped[int] = mapped_column(default=0)  # Order within the section

    # Relationships
    course = relationship("Course", back_populates="assignments")
    section = relationship("Section", back_populates="assignments")

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "section_id": self.section_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "teacher_comments": self.teacher_comments,
            "order": self.order,
        }
