from pydantic import BaseModel

from .types import Password, Token, UserEmail


class EmailPasswordRequest(BaseModel):
    email: UserEmail
    password: Password


class EmailRequest(BaseModel):
    email: UserEmail


class TokenRequest(BaseModel):
    token: Token


class TokenPasswordRequest(BaseModel):
    token: Token
    password: Password
