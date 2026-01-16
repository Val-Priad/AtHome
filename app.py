import os

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

from api.v1.auth.auth_router import bp as users_bp
from infrastructure.db import engine  # NOQA establishing connection with db

load_dotenv()

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

app.register_blueprint(users_bp)
