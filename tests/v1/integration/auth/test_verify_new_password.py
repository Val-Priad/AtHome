import secrets
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from domain.password_reset.password_reset_model import PasswordReset
from domain.user.user_model import User
from security import TokenCrypto


@pytest.fixture()
def set_token(db_session):
    user_old_hash = b"hash"
    user = User(email="user@example.com", password_hash=user_old_hash)

    db_session.add(user)
    db_session.flush()

    raw_token = secrets.token_urlsafe(32)

    password_reset = PasswordReset(
        user_id=user.id,
        token_hash=TokenCrypto.hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=5),
    )
    db_session.add(password_reset)
    db_session.flush()
    return {
        "user_id": user.id,
        "user_old_hash": user_old_hash,
        "raw_token": raw_token,
    }


def test_verify_new_password_valid(client, set_token, db_session):
    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={
            "token": set_token["raw_token"],
            "password": "new_password",
        },
    )

    assert response.status_code == 200

    user = db_session.scalar(
        select(User).where(User.id == set_token["user_id"])
    )

    user_new_password_hash = user.password_hash

    assert set_token["user_old_hash"] != user_new_password_hash

    password_reset = db_session.scalar(
        select(PasswordReset).where(
            PasswordReset.user_id == set_token["user_id"]
        )
    )

    assert datetime.now(timezone.utc) > password_reset.used_at

    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={
            "token": set_token["raw_token"],
            "password": "111111111111111",
        },
    )

    assert response.status_code == 400


def test_verify_new_password_validation(client, set_token, db_session):
    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={
            "token": set_token["raw_token"],
        },
    )

    assert response.status_code == 400

    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={"token": set_token["raw_token"], "password": ""},
    )

    assert response.status_code == 400

    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={"password": "valid_password"},
    )

    assert response.status_code == 400

    response = client.post(
        "/api/v1/auth/verify-new-password",
        json={"password": "valid_password", "token": "invalid_token"},
    )

    assert response.status_code == 400
