import logging
import re
from dataclasses import dataclass
from typing import Type

from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import HTTPException

_logger = logging.getLogger(__name__)


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


def get_description_for_exception(e: Exception) -> ErrorSpec:
    code = get_code_for_exception(e)
    return get_description(code)


def _is_external_exception(e: Exception) -> bool:
    return isinstance(e, (JWTExtendedException, HTTPException))


def _jwt_error_code(e: JWTExtendedException) -> str:
    name = e.__class__.__name__
    if name.endswith("Error"):
        name = name[:-5]

    first_rule = re.sub("(?<=[a-z])(?=[A-Z])", "_", name)
    second_rule = re.sub("(?<=[A-Z])(?=[A-Z][a-z])", "_", first_rule)
    return second_rule.lower()


def _get_http_exception_description(e: HTTPException):
    return e.description if e.description is not None else e.name


def _get_http_exception_name(e: HTTPException):
    return e.name.lower().replace(" ", "_")


def get_description_for_external_exception(e: Exception) -> ErrorSpec:
    if isinstance(e, JWTExtendedException):
        return ErrorSpec(
            status=401,
            code=_jwt_error_code(e),
            message="Authentication error",
        )
    elif isinstance(e, HTTPException):
        return ErrorSpec(
            status=e.code if e.code is not None else 500,
            message=_get_http_exception_description(e),
            code=_get_http_exception_name(e),
        )

    raise RuntimeError("Not registered external exception")


def get_code_for_exception(e: Exception) -> str:
    exc_type = type(e)
    for cls in exc_type.__mro__:
        if cls in EXCEPTION_TO_CODE:
            return EXCEPTION_TO_CODE[cls]
    _logger.exception(e)
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
    from .custom_exceptions.user_exceptions import register_user_errors
    from .custom_exceptions.validation_exceptions import (
        register_validation_errors,
    )

    register_user_errors()
    register_validation_errors()


def register_errors():
    global _INITIALIZED
    if _INITIALIZED:
        return

    _register_default_errors()
    _register_custom_errors()

    _INITIALIZED = True
