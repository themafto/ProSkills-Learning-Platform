from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "yourpassword"
            }
        }


class LoginResponse(BaseModel):
    """Schema for login response"""
    message: str = "Login successful" 