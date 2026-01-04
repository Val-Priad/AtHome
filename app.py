from dotenv import load_dotenv
from flask import Flask
from db import engine  # NOQA establishing connection with db
from api.v1.users.router import bp as users_bp
from logger import file_handler

load_dotenv()
app = Flask(__name__)

app.logger.addHandler(file_handler)

app.register_blueprint(users_bp)
