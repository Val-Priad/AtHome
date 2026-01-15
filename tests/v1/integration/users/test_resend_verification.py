from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from domain.email_verification.email_verification_model import (
    EmailVerification,
)
from domain.user.user_model import User


@pytest.fixture
def unverified_user(db_session):
    user = User(email="user@example.com", password_hash=b"hash")
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def verified_user(db_session):
    user = User(
        email="user@example.com", password_hash=b"hash", is_email_verified=True
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def previous_token(db_session, unverified_user):
    email_verification = EmailVerification(
        user_id=unverified_user.id,
        token_hash=b"hash",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(email_verification)
    db_session.flush()
    return email_verification


def test_resend_verification_valid(
    client, unverified_user, db_session, previous_token
):
    previous_token_id = previous_token.id

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": unverified_user.email},
    )

    assert response.status_code == 201

    qty_of_active_tokens = len(
        db_session.scalars(
            select(EmailVerification).where(
                EmailVerification.expires_at > datetime.now(timezone.utc),
                EmailVerification.user_id == unverified_user.id,
            )
        ).all()
    )
    assert qty_of_active_tokens == 1

    qty_of_tokens = len(
        db_session.scalars(
            select(EmailVerification).where(
                EmailVerification.user_id == unverified_user.id,
            )
        ).all()
    )
    assert qty_of_tokens == 2

    deactivated_token = db_session.scalar(
        select(EmailVerification).where(
            EmailVerification.expires_at < datetime.now(timezone.utc),
            EmailVerification.user_id == unverified_user.id,
        )
    )

    assert previous_token_id == deactivated_token.id


def test_resend_verification_validation(client):
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "invalid_email"},
    )

    assert response.status_code == 400


def test_resend_verification_if_user_not_found(client):
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "user_does_not_exist@example.com"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert "There is no user with email" in body["message"]


def test_resend_verification_if_user_already_verified(client, verified_user):
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": verified_user.email},
    )

    assert response.status_code == 409
    body = response.get_json()
    assert "was already verified" in body["message"]


def test_resend_verification_on_server_error_returns_500(
    client, unverified_user, monkeypatch
):
    def boom(db, user_id):
        raise Exception("boom")

    monkeypatch.setattr(
        "api.v1.auth.router.email_verification_service.get_resend_token", boom
    )

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": unverified_user.email},
    )

    assert response.status_code == 500
