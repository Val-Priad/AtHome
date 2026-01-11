from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

UserEmail = Annotated[EmailStr, Field(min_length=1, max_length=255)]
Password = Annotated[str, Field(min_length=1, max_length=255)]


class RegisterRequest(BaseModel):
    email: UserEmail
    password: Password


class SendNewValidationTokenRequest(BaseModel):
    email: UserEmail
