from .base import DomainError


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str):
        message = "User already exists"
        if email:
            message = f"User with email {email} already exists"
        super().__init__(message)


class UserNotFoundError(DomainError):
    def __init__(self, email: str):
        self.email = email
        message = "User does not exist"
        if email:
            message = f"User with email {email} does not exist"
        super().__init__(message)


class UserAlreadyVerifiedError(DomainError):
    def __init__(self, email: str):
        self.email = email
        message = "User was already verified"
        if email:
            message = f"User with email {email} was already verified"
        super().__init__(message)
