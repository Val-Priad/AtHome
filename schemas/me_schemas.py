from typing import Optional

from pydantic import BaseModel

from .types import (
    ImageKey,
    Password,
    PhoneNumberType,
    UserDescription,
    UserName,
)


class PasswordRequest(BaseModel):
    old_password: Password
    new_password: Password


class UpdateUserPersonalDataRequest(BaseModel):
    name: Optional[UserName]
    phone_number: Optional[PhoneNumberType]
    avatar_key: Optional[ImageKey]
    description: Optional[UserDescription]
