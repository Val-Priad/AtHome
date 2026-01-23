from typing import Annotated

from pydantic import BeforeValidator, EmailStr, Field
from pydantic_extra_types.phone_numbers import (
    PhoneNumber as PydanticPhoneNumber,
)

from .validators.user_validators import reject_string_with_whitespaces

UserName = Annotated[
    str,
    Field(min_length=1, max_length=255),
    BeforeValidator(reject_string_with_whitespaces),
]
PhoneNumberType = Annotated[PydanticPhoneNumber, Field()]
ImageKey = Annotated[str, Field(min_length=1, max_length=1024)]
UserDescription = Annotated[str, Field(min_length=1, max_length=510)]
UserEmail = Annotated[EmailStr, Field(min_length=1, max_length=255)]
Password = Annotated[
    str,
    Field(min_length=8, max_length=255),
    BeforeValidator(reject_string_with_whitespaces),
]

Token = Annotated[str, Field(min_length=40, max_length=50)]
