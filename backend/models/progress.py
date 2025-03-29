from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.models.basemodel import BaseModel


class AssignmentProgress(BaseModel):
    __tablename__ = "assignment_progress"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("our_users.id"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    submission_file_key: Mapped[str] = mapped_column(
        String, nullable=True
    )  # S3 file key for submission
    score: Mapped[int] = mapped_column(Integer, nullable=True)  # Optional score/grade
    feedback: Mapped[str] = mapped_column(String, nullable=True)  # Teacher feedback
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    student = relationship("OurUsers", backref="assignment_progress")
    assignment = relationship("Assignment", backref="student_progress")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "assignment_id": self.assignment_id,
            "is_completed": self.is_completed,
            "submission_file_key": self.submission_file_key,
            "score": self.score,
            "feedback": self.feedback,
            "completed_at": self.completed_at,
            "submitted_at": self.submitted_at,
        }


class CourseProgress(BaseModel):
    __tablename__ = "course_progress"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("our_users.id"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False
    )
    completed_assignments: Mapped[int] = mapped_column(Integer, default=0)
    total_assignments: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    student = relationship("OurUsers", backref="course_progress")
    course = relationship("Course", backref="student_progress")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "completed_assignments": self.completed_assignments,
            "total_assignments": self.total_assignments,
            "last_activity": self.last_activity,
            "completion_percentage": self.completion_percentage(),
        }

    def completion_percentage(self):
        if self.total_assignments == 0:
            return 0
        return round((self.completed_assignments / self.total_assignments) * 100, 2)
