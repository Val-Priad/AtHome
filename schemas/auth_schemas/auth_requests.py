from schemas.parent_types import RequestValidation

from ..types import Password, Token, UserEmail


class EmailPasswordRequest(RequestValidation):
    email: UserEmail
    password: Password


class EmailRequest(RequestValidation):
    email: UserEmail


class TokenRequest(RequestValidation):
    token: Token


class TokenPasswordRequest(RequestValidation):
    token: Token
    password: Password
