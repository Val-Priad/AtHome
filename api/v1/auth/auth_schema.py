from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

UserEmail = Annotated[EmailStr, Field(min_length=1, max_length=255)]
Password = Annotated[str, Field(min_length=8, max_length=255)]


class RegisterRequest(BaseModel):
    email: UserEmail
    password: Password

    @field_validator("password", mode="before")
    @classmethod
    def strip_password(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        return value


class SendNewValidationTokenRequest(BaseModel):
    email: UserEmail
