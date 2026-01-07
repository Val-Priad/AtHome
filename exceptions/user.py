from .base import DomainError


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str | None = None) -> None:
        message = "User already exists"
        if email:
            message = f"User with email {email} already exists"
        super().__init__(message)
