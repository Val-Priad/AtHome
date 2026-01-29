from functools import wraps
from typing import Callable

from .error_catalog import DomainError


def wrap_with_custom_error(
    *,
    wrap_with: type[DomainError],
    catch: type[Exception] | tuple[type[Exception], ...],
):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except catch as e:
                raise wrap_with from e

        return wrapper

    return decorator
