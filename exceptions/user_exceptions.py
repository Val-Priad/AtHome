from .error_catalog import DomainError, register_custom_error


class InvalidCredentialsError(DomainError):
    pass


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


class NewPasswordMatchesOldError(DomainError):
    pass


class MissingUpdateDataError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass


def register_user_errors():
    register_custom_error(
        UserNotFoundError, "user_not_found", 404, "User not found"
    )

    register_custom_error(
        UserIsNotVerifiedError,
        "user_not_verified",
        409,
        "Verify your email before logging in",
    )

    register_custom_error(
        PasswordVerificationError, "invalid_password", 401, "Invalid password"
    )

    register_custom_error(
        UserAlreadyVerifiedError,
        "user_already_verified",
        409,
        "User was already verified",
    )

    register_custom_error(
        TokenVerificationError, "token_invalid", 401, "Token invalid"
    )

    register_custom_error(
        UserAlreadyExistsError,
        "user_already_exists",
        409,
        "User with such email already exists",
    )

    register_custom_error(
        NewPasswordMatchesOldError,
        "new_password_matches_old",
        409,
        "New password must be different from the old password",
    )

    register_custom_error(
        MissingUpdateDataError,
        "missing_data_for_update",
        400,
        "Missing data for updating personal information",
    )

    register_custom_error(
        InvalidCredentialsError,
        "invalid_credentials",
        401,
        "Invalid credentials",
    )

    register_custom_error(
        ForbiddenError,
        "forbidden",
        403,
        "Forbidden action",
    )
