from pydantic import BaseModel, EmailStr, Field


class CreateUserSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    fullname: str

class LoginUserSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponseSchema(BaseModel):
    user_id: int
    email: EmailStr
    fullname: str
