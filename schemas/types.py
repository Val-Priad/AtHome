from typing import Annotated

from pydantic import BeforeValidator, EmailStr, Field

from .validators.user_validators import reject_password_with_whitespaces

UserEmail = Annotated[EmailStr, Field(min_length=1, max_length=255)]
Password = Annotated[
    str,
    Field(min_length=8, max_length=255),
    BeforeValidator(reject_password_with_whitespaces),
]
Token = Annotated[str, Field(min_length=40, max_length=50)]
