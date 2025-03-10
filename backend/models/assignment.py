from datetime import datetime
from typing import Optional

from backend.models.basemodel import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey


class Assignment(BaseModel):
    __tablename__ = 'assignments'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id'), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    teacher_comments: Mapped[str] = mapped_column(String, default="")