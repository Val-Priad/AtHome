import pytest
from conftest import API_PREFIX, AUTH_ENDPOINT_PATH
from sqlalchemy import select

from domain.user.user_model import User


@pytest.fixture()
def verified_user(db_session, client):
    email = "user@example.com"
    password = "12345678"
    response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 202

    user = db_session.scalar(select(User).where(User.email == email))
    user.is_email_verified = True
    db_session.flush()
    return {"email": email, "password": password}


@pytest.fixture
def unverified_user(client, db_session):
    email = "user@example.com"
    password = "12345678"
    response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 202

    return {"email": email, "password": password}


def test_login_and_log_out(client, verified_user):
    login_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        json={
            "email": verified_user["email"],
            "password": verified_user["password"],
        },
    )
    assert login_response.status_code == 200

    csrf = client.get_cookie("csrf_access_token").value

    logout_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/logout",
        headers={"X-CSRF-TOKEN": csrf},
    )
    assert logout_response.status_code == 200


def test_login_unverified_user(client, unverified_user):
    login_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        json={
            "email": unverified_user["email"],
            "password": unverified_user["password"],
        },
    )
    assert login_response.status_code == 401


def test_login_not_registered_user(client):
    login_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        json={
            "email": "not_registered@example.com",
            "password": "not_registered",
        },
    )
    assert login_response.status_code == 401


def test_login_invalid_password(client, verified_user):
    login_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        json={
            "email": verified_user["email"],
            "password": "wrong_password",
        },
    )
    assert login_response.status_code == 401
