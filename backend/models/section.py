from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.basemodel import BaseModel


class Section(BaseModel):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # Order within the course
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )

    # Relationships
    course = relationship("Course", back_populates="sections")
    assignments = relationship(
        "Assignment",
        back_populates="section",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "order": self.order,
            "course_id": self.course_id,
        }
