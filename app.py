from flask import Flask

from api.v1.admin.users.admin_users_router import bp as admin_users_bp
from api.v1.auth.auth_router import bp as auth_bp
from api.v1.users.me.me_router import bp as me_bp
from config import DevelopmentConfig, FlaskConfig
from exceptions.error_catalog import register_errors
from infrastructure.db import get_engine
from infrastructure.jwt.jwt_config import create_jwt_manager
from infrastructure.jwt.jwt_handlers import register_jwt_handlers
from infrastructure.logging.setup_logging import setup_logging
from infrastructure.rate_limiting.limiter_config import create_limiter


def create_app(config: type[FlaskConfig]) -> Flask:
    setup_logging()
    app = Flask(__name__)

    app.config.from_object(config)

    register_errors()

    get_engine()

    create_limiter(app)
    create_jwt_manager(app)

    register_jwt_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(admin_users_bp)

    return app


app = create_app(DevelopmentConfig)
