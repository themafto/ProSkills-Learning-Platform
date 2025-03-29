from sqlalchemy import Column, Integer, String, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.models.basemodel import BaseModel
from backend.models.enrollment import Enrollment
from sqlalchemy.sql.schema import ForeignKey


class Course(BaseModel):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    lessons_count: Mapped[int] = mapped_column(Integer)
    lessons_duration: Mapped[int] = mapped_column(Integer)
    rating: Mapped[int] = mapped_column(Integer)
    ratings_count: Mapped[int] = mapped_column(Integer, default=0)
    files = Column(ARRAY(String))  # Для PostgreSQL
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("our_users.id"), nullable=False
    )

    teacher = relationship(
        "OurUsers", back_populates="courses_teaching", foreign_keys=[teacher_id]
    )
    students = relationship(
        "OurUsers", secondary=Enrollment.__table__, back_populates="courses"
    )
    sections = relationship(
        "Section",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.order",
    )
    assignments = relationship(
        "Assignment", back_populates="course", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "lessons_count": self.lessons_count,
            "lessons_duration": self.lessons_duration,
            "rating": self.rating,
            "ratings_count": self.ratings_count,
            "files": self.files,
            "teacher_id": self.teacher_id,
        }
