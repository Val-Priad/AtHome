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


def test_login_and_log_out(client, verified_user):
    login_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        json={
            "email": verified_user["email"],
            "password": verified_user["password"],
        },
    )
    assert login_response.status_code == 204

    csrf = client.get_cookie("csrf_access_token").value

    logout_response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/logout",
        headers={"X-CSRF-TOKEN": csrf},
    )
    assert logout_response.status_code == 204
