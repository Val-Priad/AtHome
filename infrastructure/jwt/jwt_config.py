from flask import Flask
from flask_jwt_extended import (
    JWTManager,
)

jwt = JWTManager()


def create_jwt_manager(app: Flask):
    jwt.init_app(app)
