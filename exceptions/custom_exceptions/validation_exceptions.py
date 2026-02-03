from ..error_catalog import DomainError, register_custom_error


class ValidationError(DomainError):
    pass


class RequestValidationError(ValidationError):
    pass


class ResponseValidationError(ValidationError):
    pass


def register_validation_errors():
    register_custom_error(
        RequestValidationError,
        "request_validation_error",
        400,
        "Invalid input",
    )

    register_custom_error(
        ResponseValidationError,
        "response_validation_error",
        500,
        "Internal server error",
    )
