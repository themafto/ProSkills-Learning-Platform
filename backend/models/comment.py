from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.basemodel import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("our_users.id"), nullable=False)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id"),
        nullable=False,
    )
    comment_text: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
    )
