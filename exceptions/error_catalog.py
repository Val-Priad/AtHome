from __future__ import annotations

from dataclasses import dataclass
from typing import Type


class DomainError(Exception):
    """Base class for domain errors"""


@dataclass(frozen=True)
class ErrorSpec:
    status: int
    message: str
    code: str


_INITIALIZED = False
ERROR_CATALOG: dict[str, ErrorSpec] = {}
EXCEPTION_TO_CODE: dict[Type[Exception], str] = {}
DEFAULT_ERROR_CODE = "internal_server_error"


def map_code(code: str, status: int, message: str):
    if code in ERROR_CATALOG:
        raise ValueError(f"Error code already registered: {code}")
    ERROR_CATALOG[code] = ErrorSpec(status=status, message=message, code=code)


def map_exception(exception_type: Type[Exception], code: str):
    if exception_type in EXCEPTION_TO_CODE:
        raise ValueError(
            f"Exception already mapped: {exception_type.__name__}"
        )
    EXCEPTION_TO_CODE[exception_type] = code


def get_description(code: str) -> ErrorSpec:
    return ERROR_CATALOG[code]


def get_description_for_exception(exception: Exception) -> ErrorSpec:
    code = get_code_for_exception(exception)
    return get_description(code)


def get_code_for_exception(exception: Exception) -> str:
    exc_type = type(exception)
    for cls in exc_type.__mro__:
        if cls in EXCEPTION_TO_CODE:
            return EXCEPTION_TO_CODE[cls]
    return DEFAULT_ERROR_CODE


def register_custom_error(
    exception_type: Type[Exception], code: str, status: int, message: str
):
    map_exception(exception_type, code)
    map_code(code, status, message)


def _register_default_errors():
    map_code("validation_error", 400, "Validation error")
    map_code(DEFAULT_ERROR_CODE, 500, "Internal server error")


def _register_custom_errors():
    from .user_exceptions import register_user_errors
    from .validation_exceptions import register_validation_errors

    register_user_errors()
    register_validation_errors()


def register_errors():
    global _INITIALIZED
    if _INITIALIZED:
        return

    _register_default_errors()
    _register_custom_errors()

    _INITIALIZED = True
