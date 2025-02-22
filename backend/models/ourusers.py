from sqlalchemy.orm import relationship

from backend.database import Base
from sqlalchemy import Column, Integer, String, Boolean


class OurUsers(Base):
    __tablename__ = 'our_users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default='student')

    courses = relationship("Course", back_populates="users")

