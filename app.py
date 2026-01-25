from flask import Flask

from api.v1.auth.auth_router import bp as auth_bp
from api.v1.users.me.me_router import bp as me_bp
from config import DevelopmentConfig, FlaskConfig
from exceptions import initialize_custom_exceptions  # noqa: F401
from infrastructure.db import engine  # NOQA establishing connection with db
from infrastructure.jwt.jwt_config import create_jwt_manager
from infrastructure.jwt.jwt_handlers import register_jwt_handlers
from infrastructure.rate_limiting.limiter_config import create_limiter


def create_app(config: type[FlaskConfig]) -> Flask:
    app = Flask(__name__)

    app.config.from_object(config)

    create_limiter(app)
    create_jwt_manager(app)

    register_jwt_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)

    return app


app = create_app(DevelopmentConfig)
