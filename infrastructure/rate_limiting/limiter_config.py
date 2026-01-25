from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address)


def create_limiter(app: Flask):
    limiter.init_app(app)
