from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role: str


    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "<NAME>",
                "email": "<EMAIL>",
                'password': '<PASSWORD>',
            }
        }