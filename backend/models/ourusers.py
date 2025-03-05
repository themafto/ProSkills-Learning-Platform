from sqlalchemy.orm import relationship, Mapped, mapped_column

from sqlalchemy import Column, Integer, String, Boolean

from backend.models.basemodel import BaseModel
from backend.models.enrollment import Enrollment
from backend.roles import UserRole


class OurUsers(BaseModel):
    __tablename__ = 'our_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default=UserRole.STUDENT.value)

    courses = relationship("Course",secondary=Enrollment.__table__, back_populates="students")
    courses_teaching = relationship("Course", back_populates="teacher")

