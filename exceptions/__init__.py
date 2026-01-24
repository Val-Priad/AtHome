from .error_catalog import get_code_for_exception, get_description
from .mailer_exceptions import EmailSendError
from .user_exceptions import (
    NewPasswordMatchesOldError,
    PasswordVerificationError,
    TokenVerificationError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserIsNotVerifiedError,
    UserNotFoundError,
    MissingUpdateDataError,
)

__all__ = [
    "get_description",
    "get_code_for_exception",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "UserAlreadyVerifiedError",
    "UserIsNotVerifiedError",
    "TokenVerificationError",
    "PasswordVerificationError",
    "EmailSendError",
    "NewPasswordMatchesOldError",
    "MissingUpdateDataError",
]
