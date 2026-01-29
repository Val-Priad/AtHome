from pydantic import BaseModel, ConfigDict, ValidationError

from domain.user.user_model import User
from exceptions.validation_exceptions import ResponseValidationError
from schemas.types import (
    ID,
    E164PhoneNumberType,
    ImageKey,
    UserDescription,
    UserEmail,
    UserName,
    UserRole,
)


class UserResponse(BaseModel):
    id: ID
    email: UserEmail
    role: UserRole

    name: UserName | None
    phone_number: E164PhoneNumberType | None
    avatar_key: ImageKey | None
    description: UserDescription | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, user: User):
        try:
            return cls.model_validate(user)
        except ValidationError as e:
            raise ResponseValidationError() from e
