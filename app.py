import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from api.v1.auth.auth_router import bp as auth_bp
from api.v1.users.me.me_router import bp as me_bp
from exceptions import initialize_custom_exceptions  # noqa: F401
from infrastructure.db import engine  # NOQA establishing connection with db
from infrastructure.jwt.jwt_config import jwt
from infrastructure.jwt.jwt_handlers import register_jwt_handlers
from infrastructure.rate_limiting.limiter_config import limiter


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_COOKIE_SECURE"] = (
        False  # TODO: Change it in production to true
    )
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    limiter.init_app(app)
    jwt.init_app(app)

    register_jwt_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)

    return app


app = create_app()
