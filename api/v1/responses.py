from flask import Response, jsonify, make_response

from exceptions.error_catalog import get_description


def construct_response(data=None, message="OK", status=200) -> Response:
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return make_response(jsonify(payload), status)


def construct_error(code: str) -> Response:
    description = get_description(code)
    return make_response(
        jsonify({"error": {"code": code, "message": description.message}}),
        description.status,
    )
