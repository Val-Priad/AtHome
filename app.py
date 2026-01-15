from dotenv import load_dotenv
from flask import Flask

from api.v1.auth.auth_router import bp as users_bp
from infrastructure.db import engine  # NOQA establishing connection with db

load_dotenv()
app = Flask(__name__)

app.register_blueprint(users_bp)
