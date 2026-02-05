from pydantic import ConfigDict

from domain.user.user_model import UserRole
from schemas.parent_types import ResponseValidation
from schemas.types import (
    ID,
    E164PhoneNumberType,
    ImageKey,
    UserDescription,
    UserEmail,
    UserName,
)


class MeResponse(ResponseValidation):
    id: ID
    email: UserEmail
    role: UserRole

    name: UserName | None
    phone_number: E164PhoneNumberType | None
    avatar_key: ImageKey | None
    description: UserDescription | None

    model_config = ConfigDict(from_attributes=True)
