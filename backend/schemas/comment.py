from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    comment_text: str


class CommentResponse(CommentCreate):
    id: int
    user_id: int
    assignment_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
