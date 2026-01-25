from datetime import datetime, timedelta, timezone

from flask import Flask, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
)


def register_jwt_handlers(app: Flask):
    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            if request.path == "/api/v1/auth/logout":
                return response

            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token)
            return response
        except (RuntimeError, KeyError):
            return response
