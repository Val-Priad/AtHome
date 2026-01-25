import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import event, select
from sqlalchemy.orm import Session, sessionmaker

from app import create_app
from config import TestingConfig
from domain.user.user_model import User
from infrastructure.db import engine

API_PREFIX = "/api/v1"
AUTH_ENDPOINT_PATH = "/auth"
ME_ENDPOINT_PATH = "/users/me"


@pytest.fixture
def app() -> Flask:
    return create_app(TestingConfig)


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

        monkeypatch.setattr("api.v1.auth.auth_router.session", lambda: db)
        monkeypatch.setattr("api.v1.users.me.me_router.session", lambda: db)

        @event.listens_for(db, "after_transaction_end")
        def restart_savepoint(session, transaction_):
            if transaction_.nested:
                session.begin_nested()

        yield db

        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def logged_in_user(client: FlaskClient, db_session: Session):
    email = "user@example.com"
    password = "12345678"
    payload = {"email": email, "password": password}
    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 202

    user = db_session.scalar(select(User).where(User.email == email))
    assert user is not None

    user.is_email_verified = True
    user.phone_number = "+420701234567"
    user.name = "Val Priad"
    user.avatar_key = "avatars/default/user_1.png"
    user.description = "Test user account for integration tests"
    db_session.flush()

    login_response = client.post("/api/v1/auth/login", json=payload)
    assert login_response.status_code == 200

    cookie = client.get_cookie("csrf_access_token")
    assert cookie is not None

    return {
        "email": email,
        "password": password,
        "headers": {"X-CSRF-TOKEN": cookie.value},
    }
