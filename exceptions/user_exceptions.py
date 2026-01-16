from .error_catalog import DomainError, register_custom_error


class UserAlreadyExistsError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class UserAlreadyVerifiedError(DomainError):
    pass


class UserIsNotVerifiedError(DomainError):
    pass


class TokenVerificationError(DomainError):
    pass


class PasswordVerificationError(DomainError):
    pass


def _register_user_errors():
    register_custom_error(
        UserNotFoundError, "user_not_found", 400, "User not found"
    )

    register_custom_error(
        UserIsNotVerifiedError,
        "user_not_verified",
        403,
        "Verify your email before logging in",
    )

    register_custom_error(
        PasswordVerificationError, "invalid_password", 400, "Invalid password"
    )

    register_custom_error(
        UserAlreadyVerifiedError,
        "user_already_verified",
        409,
        "User was already verified",
    )

    register_custom_error(
        TokenVerificationError, "token_invalid", 400, "Token invalid"
    )

    register_custom_error(
        UserAlreadyExistsError,
        "user_already_exists",
        409,
        "User with such email already exists",
    )


_register_user_errors()
