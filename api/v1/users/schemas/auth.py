from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
