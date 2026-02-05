from types import SimpleNamespace

from flask import Flask
from flask.testing import FlaskClient
from pytest import FixtureRequest, fixture
from sqlalchemy import event, select
from sqlalchemy.orm import Session, sessionmaker

from app import create_app
from config import TestingConfig
from domain.user.user_model import User, UserRole
from infrastructure import db as db_module
from security.password_crypto import PasswordCrypto

API_PREFIX = "/api/v1"
AUTH_ENDPOINT_PATH = "/auth"
ME_ENDPOINT_PATH = "/users/me"
ADMIN_USERS_PATH = "/admin/users"


@fixture
def app() -> Flask:
    return create_app(TestingConfig)


@fixture
def client(app) -> FlaskClient:
    return app.test_client()


@fixture(autouse=True)
def noop_send_verification_email(monkeypatch):
    monkeypatch.setattr(
        "infrastructure.email.Mailer.Mailer.send_verification_email",
        lambda *args, **kwargs: None,
    )


@fixture(autouse=True)
def db_session(app: Flask, monkeypatch):
    with app.app_context():
        engine = db_module.get_engine()
        connection = engine.connect()
        transaction = connection.begin()

        TestingSessionFactory = sessionmaker(bind=connection)
        session = TestingSessionFactory()
        session.begin_nested()

        monkeypatch.setattr(
            db_module, "_SessionFactory", TestingSessionFactory
        )

        @event.listens_for(session, "after_transaction_end")
        def restart_savepoint(session, transaction_):
            if transaction_.nested:
                session.begin_nested()

        yield session

        session.close()
        transaction.rollback()
        connection.close()


@fixture
def logged_in_user(
    request: FixtureRequest, client: FlaskClient, db_session: Session
):
    user_role = getattr(request, "param", UserRole.user)

    email = "logged_in_user@example.com"
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
    user.role = user_role
    db_session.flush()

    login_response = client.post("/api/v1/auth/login", json=payload)
    assert login_response.status_code == 200

    cookie = client.get_cookie("csrf_access_token")
    assert cookie is not None

    return SimpleNamespace(
        id=user.id,
        email=email,
        password=password,
        headers={"X-CSRF-TOKEN": cookie.value},
    )


@fixture
def any_user(request: FixtureRequest, db_session: Session):
    user_role = getattr(request, "param", UserRole.user)

    user = User(
        email="any_user@example.com",
        password_hash=PasswordCrypto.hash_password("any_password"),
        is_email_verified=True,
        role=user_role,
    )
    db_session.add(user)
    db_session.flush()
    return user
