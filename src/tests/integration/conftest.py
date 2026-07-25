import os
from collections.abc import Iterator
from types import SimpleNamespace
from typing import cast

from dotenv import load_dotenv
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, decode_token
from pytest import FixtureRequest, fixture
from sqlalchemy import Table
from sqlalchemy.orm import Session, sessionmaker

from app import create_app
from composition.application_container import ApplicationContainer
from composition.build_application_container import build_application_container
from composition.container_access import APPLICATION_CONTAINER_KEY
from composition.dependency_overrides import DependencyOverrides
from config import TestingConfig
from domain.media.media_enums import MediaPurpose, MediaType
from domain.media.media_upload_model import MediaUpload
from domain.user.services.password_hasher import PasswordHasher
from domain.user.user_model import User, UserRole
from infrastructure.db import Base, db
from tests.integration.fake_infrastructure.fake_mailer import FakeMailer
from tests.integration.fake_infrastructure.fake_object_storage import (
    FakeObjectStorage,
)
from tests.integration.fake_infrastructure.fake_vicinity_client import (
    FakeVicinityClient,
)
from tests.integration.testing_blueprint import testing_bp

ME_PATH = "/api/users/me"
AGENTS_PATH = "/api/agents"
ESTATE_PATH = "/api/estate"
AUTH_PATH = "/api/auth"
ADMIN_USERS_PATH = "/api/admin/users"
ADMIN_AGENTS_PATH = "/api/admin/agents"
ADMIN_ESTATE_PATH = "/api/admin/estate"
MEDIA_PATH = "/api/media"
TEST_PASSWORD = "any_password"


@fixture(scope="session")
def fake_mailer() -> FakeMailer:
    return FakeMailer()


@fixture(scope="session")
def fake_vicinity_client() -> FakeVicinityClient:
    return FakeVicinityClient()


@fixture(scope="session")
def fake_object_storage() -> FakeObjectStorage:
    return FakeObjectStorage()


@fixture(scope="session")
def app(
    fake_mailer: FakeMailer,
    fake_vicinity_client: FakeVicinityClient,
    fake_object_storage: FakeObjectStorage,
) -> Iterator[Flask]:
    load_dotenv()
    test_database_url = os.environ["TEST_DATABASE_URL"]

    app = create_app(
        TestingConfig,
        config_overrides={
            "DATABASE_URL": test_database_url,
            "JWT_SECRET_KEY": "test-secret-key-at-least-32-bytes-long",
            "APP_BASE_URL": "https://athome.test",
            "MEDIA_BASE_URL": "https://media.test",
        },
        dependency_overrides=DependencyOverrides(
            mailer=fake_mailer,
            vicinity_client=fake_vicinity_client,
            object_storage=fake_object_storage,
        ),
    )

    app.register_blueprint(testing_bp)
    Base.metadata.create_all(
        db.get_engine(app),
        tables=[cast(Table, MediaUpload.__table__)],
        checkfirst=True,
    )

    try:
        yield app
    finally:
        db.dispose(app)


@fixture
def client(app) -> FlaskClient:
    return app.test_client()


@fixture(autouse=True)
def db_session(
    app: Flask,
    fake_mailer: FakeMailer,
    fake_vicinity_client: FakeVicinityClient,
    fake_object_storage: FakeObjectStorage,
) -> Iterator[Session]:
    fake_mailer.reset()
    fake_object_storage.reset()

    with app.app_context():
        engine = db.get_engine(app)
        connection = engine.connect()
        transaction = connection.begin()

        testing_session_factory = sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        original_container = app.extensions[APPLICATION_CONTAINER_KEY]
        app.extensions[APPLICATION_CONTAINER_KEY] = (
            build_application_container(
                app,
                overrides=DependencyOverrides(
                    session_factory=testing_session_factory,
                    mailer=fake_mailer,
                    vicinity_client=fake_vicinity_client,
                    object_storage=fake_object_storage,
                ),
            )
        )

        session = testing_session_factory()

        try:
            yield session
        finally:
            session.close()
            app.extensions[APPLICATION_CONTAINER_KEY] = original_container
            transaction.rollback()
            connection.close()


@fixture
def application_container(app: Flask) -> ApplicationContainer:
    return app.extensions[APPLICATION_CONTAINER_KEY]


@fixture
def reserve_media_upload(db_session: Session):
    def reserve(
        object_key: str,
        uploader_id,
        *,
        purpose: MediaPurpose,
        media_type: MediaType = MediaType.image,
    ) -> MediaUpload:
        prefix, filename = object_key.rsplit("/", maxsplit=1)
        upload = MediaUpload(
            object_key=object_key,
            upload_object_key=f"{prefix}/pending/{filename}",
            uploader_id=uploader_id,
            purpose=purpose,
            media_type=media_type,
        )
        db_session.add(upload)
        db_session.flush()
        return upload

    return reserve


@fixture(scope="session")
def test_password_hash() -> bytes:
    return PasswordHasher.hash_password(TEST_PASSWORD)


@fixture
def logged_in_user(
    request: FixtureRequest,
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    test_password_hash: bytes,
):
    user_role = getattr(request, "param", UserRole.user)

    user = User(
        email="logged_in_user@example.com",
        password_hash=test_password_hash,
        is_email_verified=True,
        phone_number="+420701234567",
        name="Val Priad",
        avatar_key="avatars/default/user_1.png",
        description="Test user account for integration tests",
        role=user_role,
    )
    db_session.add(user)
    db_session.flush()

    access_token = create_access_token(identity=str(user.id), fresh=True)
    csrf_token = decode_token(access_token)["csrf"]

    client.set_cookie(
        key=app.config["JWT_ACCESS_COOKIE_NAME"],
        value=access_token,
        path=app.config["JWT_ACCESS_COOKIE_PATH"],
    )
    client.set_cookie(
        key=app.config["JWT_ACCESS_CSRF_COOKIE_NAME"],
        value=csrf_token,
        path=app.config["JWT_ACCESS_CSRF_COOKIE_PATH"],
    )

    return SimpleNamespace(
        id=user.id,
        role=user.role,
        email=user.email,
        password=TEST_PASSWORD,
        headers={app.config["JWT_ACCESS_CSRF_HEADER_NAME"]: csrf_token},
    )


@fixture
def any_user(
    request: FixtureRequest,
    db_session: Session,
    test_password_hash: bytes,
):
    user_role = getattr(request, "param", UserRole.user)

    user = User(
        email="any_user@example.com",
        password_hash=test_password_hash,
        is_email_verified=True,
        role=user_role,
    )
    db_session.add(user)
    db_session.flush()
    return user
