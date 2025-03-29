from pydantic import BaseModel


class RatingCreate(BaseModel):
    rating: int
    course_id: int


class RatingResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    rating: int
