from dotenv import load_dotenv
from flask import Flask
from db import engine  # NOQA establishing connection with db
from api.v1.users.router import bp as users_bp

load_dotenv()
app = Flask(__name__)

app.register_blueprint(users_bp)
