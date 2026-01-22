from pydantic import BaseModel

from .types import Password


class PasswordRequest(BaseModel):
    password: Password
