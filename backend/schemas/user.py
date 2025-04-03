import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    role: str = Field(default="student")

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase character")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase character")
        if not re.search("[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class UserLoginResponse(BaseModel):
    email: EmailStr
    id: int
    role: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class UserLoginResponseAuth(BaseModel):
    email: EmailStr
    id: int
    role: str

    class Config:
        orm_mode = True


class TeacherOfCourse(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool
