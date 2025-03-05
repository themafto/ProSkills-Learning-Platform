from sqlalchemy import Column, Integer, String, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.models.basemodel import BaseModel
from backend.models.enrollment import Enrollment
from sqlalchemy.sql.schema import ForeignKey

class Course(BaseModel):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    lessons_count: Mapped[int] = mapped_column(Integer)
    lessons_duration: Mapped[int] = mapped_column(Integer)
    rating: Mapped[int] = mapped_column(Integer)
    files = Column(ARRAY(String))  # Для PostgreSQL
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey('our_users.id'), nullable=False)

    teacher = relationship("OurUsers", back_populates="courses_teaching", foreign_keys=[teacher_id])
    students = relationship("OurUsers", secondary=Enrollment.__table__, back_populates="courses")
