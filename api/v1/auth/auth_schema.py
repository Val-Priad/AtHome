from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

UserEmail = Annotated[EmailStr, Field(min_length=1, max_length=255)]
Password = Annotated[str, Field(min_length=8, max_length=255)]
Token = Annotated[str, Field(min_length=40, max_length=50)]


class EmailPasswordRequest(BaseModel):
    email: UserEmail
    password: Password

    @field_validator("password", mode="before")
    @classmethod
    def strip_password(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        return value


class EmailRequest(BaseModel):
    email: UserEmail


class TokenRequest(BaseModel):
    token: Token


class TokenPasswordRequest(BaseModel):
    token: Token
    password: Password
