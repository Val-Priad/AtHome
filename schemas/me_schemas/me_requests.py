from typing import Optional

from pydantic import BaseModel

from ..types import (
    E164PhoneNumberType,
    ImageKey,
    Password,
    UserDescription,
    UserName,
)


class PasswordRequest(BaseModel):
    old_password: Password
    new_password: Password


class UpdateUserPersonalDataRequest(BaseModel):
    name: Optional[UserName] = None
    phone_number: Optional[E164PhoneNumberType] = None
    avatar_key: Optional[ImageKey] = None
    description: Optional[UserDescription] = None
