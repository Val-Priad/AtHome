import secrets
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from domain.email_verification.email_verification_model import (
    EmailVerification,
)
from domain.email_verification.email_verification_service import (
    EmailVerificationService,
)
from domain.user.user_model import User


@pytest.fixture
def raw_token_verification_id_user_id(db_session):
    user = User(email="user@example.com", password_hash=b"hash")
    db_session.add(user)
    db_session.flush()

    raw_token = secrets.token_urlsafe(32)
    hashed_token = EmailVerificationService._get_hashed_token(raw_token)
    email_verification = EmailVerification(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(email_verification)
    db_session.flush()
    return raw_token, email_verification.id, user.id


@pytest.fixture
def expired_raw_token_verification_id_user_id(db_session):
    user = User(email="user@example.com", password_hash=b"hash")
    db_session.add(user)
    db_session.flush()

    raw_token = secrets.token_urlsafe(32)
    hashed_token = EmailVerificationService._get_hashed_token(raw_token)
    email_verification = EmailVerification(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=24),
    )
    db_session.add(email_verification)
    db_session.flush()
    return raw_token, email_verification.id, user.id


def test_token_verification_valid(
    client, raw_token_verification_id_user_id, db_session
):
    raw_token, email_verification_id, user_id = (
        raw_token_verification_id_user_id
    )

    now = datetime.now(timezone.utc)

    response = client.post(
        "api/v1/auth/verify-email", json={"token": raw_token}
    )
    assert response.status_code == 200

    email_verification = db_session.scalar(
        select(EmailVerification).where(
            EmailVerification.id == email_verification_id
        )
    )
    assert email_verification.used_at >= now

    user = db_session.scalar(select(User).where(User.id == user_id))
    assert user.is_email_verified


def test_token_verification_token_validation(client):
    response = client.post("api/v1/auth/verify-email", json={"token": ""})
    assert response.status_code == 400

    too_long = "" * 55
    response = client.post(
        "api/v1/auth/verify-email", json={"token": too_long}
    )
    assert response.status_code == 400

    response = client.post("api/v1/auth/verify-email", json={"token": 67})
    assert response.status_code == 400

    response = client.post("api/v1/auth/verify-email", json={})
    assert response.status_code == 400


def test_token_verification_token_expired(
    client, expired_raw_token_verification_id_user_id
):
    raw_token, _, _ = expired_raw_token_verification_id_user_id

    response = client.post(
        "api/v1/auth/verify-email", json={"token": raw_token}
    )
    assert response.status_code == 400

    body = response.get_json()
    assert "Token invalid" in body["message"]
