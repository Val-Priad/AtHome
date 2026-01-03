from dotenv import load_dotenv
from flask import Flask
from db import engine  # NOQA establishing connection with db

load_dotenv()
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello World</p>"
