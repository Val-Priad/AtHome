from flask import Response, jsonify, make_response

from exceptions.error_catalog import (
    get_description,
    get_description_for_exception,
)


def construct_response(data=None, message="OK", status=200) -> Response:
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return make_response(jsonify(payload), status)


def construct_no_content() -> Response:
    return Response(status=204)


def construct_error(
    e: Exception | None = None, code: str | None = None
) -> Response:
    if code is not None:
        description = get_description(code)
    elif e is not None:
        description = get_description_for_exception(e)
    else:
        raise ValueError("Exception or code must be provided")

    return make_response(
        jsonify(
            {
                "error": {
                    "code": description.code,
                    "message": description.message,
                }
            }
        ),
        description.status,
    )
