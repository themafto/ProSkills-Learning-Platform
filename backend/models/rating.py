from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.basemodel import BaseModel

class Rating(BaseModel):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("our_users.id"))
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("OurUsers", backref="course_ratings")
    course = relationship("Course", backref="ratings")