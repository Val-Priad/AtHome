import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
)

from api.v1.auth.auth_router import bp as auth_bp
from api.v1.users.me.me_router import bp as me_bp
from exceptions import initialize_custom_exceptions  # noqa: F401
from infrastructure.db import engine  # NOQA establishing connection with db

load_dotenv()

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_COOKIE_SECURE"] = (
    False  # TODO: Change it in production to true
)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)


jwt = JWTManager(app)


@app.after_request
def refresh_expiring_jwts(response):
    try:
        if request.path == "/api/v1/auth/logout":
            return response

        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=60))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response


app.register_blueprint(auth_bp)
app.register_blueprint(me_bp)
