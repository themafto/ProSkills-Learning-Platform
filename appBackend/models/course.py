from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from appBackend.db.session import Base


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    lessons_count: Mapped[int] = mapped_column(Integer)
    lessons_duration: Mapped[int] = mapped_column(Integer)
    files = Column(ARRAY(String))  # Для PostgreSQL
    teacher_id = Column(Integer, ForeignKey('our_users.id'))

    users = relationship("OurUsers", back_populates="courses")