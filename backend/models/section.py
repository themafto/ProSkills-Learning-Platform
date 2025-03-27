from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.models.basemodel import BaseModel

class Section(BaseModel):
    __tablename__ = 'sections'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # Order within the course
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)
    
    # Relationships
    course = relationship("Course", back_populates="sections")
    assignments = relationship("Assignment", back_populates="section", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "course_id": self.course_id
        } 