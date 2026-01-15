import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app import app as flask_app
from infrastructure.db import engine


@pytest.fixture
def app() -> Flask:
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()


@pytest.fixture(autouse=True)
def noop_send_verification_email(monkeypatch):
    monkeypatch.setattr(
        "infrastructure.email.Mailer.Mailer.send_verification_email",
        lambda *args, **kwargs: None,
    )


@pytest.fixture(autouse=True)
def db_session(app: Flask, monkeypatch):
    with app.app_context():
        connection = engine.connect()
        transaction = connection.begin()

        session = sessionmaker(bind=connection)
        db = session()
        db.begin_nested()

        monkeypatch.setattr("api.v1.auth.router.session", lambda: db)

        @event.listens_for(db, "after_transaction_end")
        def restart_savepoint(session, transaction_):
            if transaction_.nested:
                session.begin_nested()

        yield db

        db.close()
        transaction.rollback()
        connection.close()
