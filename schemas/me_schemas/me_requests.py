from typing import Optional

from schemas.parent_types import RequestValidation
from schemas.types import (
    E164PhoneNumberType,
    ImageKey,
    Password,
    UserDescription,
    UserName,
)


class PasswordRequest(RequestValidation):
    old_password: Password
    new_password: Password


class UpdateUserPersonalDataRequest(RequestValidation):
    name: Optional[UserName] = None
    phone_number: Optional[E164PhoneNumberType] = None
    avatar_key: Optional[ImageKey] = None
    description: Optional[UserDescription] = None
