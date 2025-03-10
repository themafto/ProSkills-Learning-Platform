import sqlalchemy
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Enrollment(Base):
    __tablename__ = "enrollment"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("our_users.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), primary_key=True)

    ### Preventing Duplicate Course Enrollment ###
    __table_args__ = (sqlalchemy.UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),)