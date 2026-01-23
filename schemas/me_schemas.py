from pydantic import BaseModel

from .types import Password


class PasswordRequest(BaseModel):
    old_password: Password
    new_password: Password
