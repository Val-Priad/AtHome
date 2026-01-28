import pytest
from conftest import API_PREFIX, ME_ENDPOINT_PATH
from sqlalchemy import select

from domain.user.user_model import User
from exceptions.user_exceptions import PasswordVerificationError
from security.password_crypto import PasswordCrypto


def test_update_user_password_valid(client, db_session, logged_in_user):
    new_password = "new-password"
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update_password",
        json={
            "old_password": logged_in_user["password"],
            "new_password": new_password,
        },
        headers=logged_in_user["headers"],
    )

    assert response.status_code == 200

    db_session.expire_all()
    user = db_session.scalar(
        select(User).where(User.email == logged_in_user["email"])
    )

    with pytest.raises(PasswordVerificationError):
        PasswordCrypto.verify_password(
            logged_in_user["password"], user.password_hash
        )

    PasswordCrypto.verify_password(new_password, user.password_hash)


def test_update_user_password_old_password_matches_new(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update_password",
        json={
            "old_password": logged_in_user["password"],
            "new_password": logged_in_user["password"],
        },
        headers=logged_in_user["headers"],
    )

    assert response.status_code == 409


def test_update_user_password_old_password_is_wrong(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update_password",
        json={
            "old_password": "invalid-old-password",
            "new_password": logged_in_user["password"],
        },
        headers=logged_in_user["headers"],
    )

    assert response.status_code == 401
