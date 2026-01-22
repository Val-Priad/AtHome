import pytest
from sqlalchemy import select

from domain.user import User


@pytest.fixture()
def verified_user(db_session, client):
    email = "user@example.com"
    password = "12345678"
    response = client.post(
        "api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201

    user = db_session.scalar(select(User).where(User.email == email))
    user.is_email_verified = True
    db_session.flush()
    return {"email": email, "password": password}


def test_login_and_log_out(client, verified_user):
    login_response = client.post(
        "api/v1/auth/login",
        json={
            "email": verified_user["email"],
            "password": verified_user["password"],
        },
    )
    assert login_response.status_code == 200

    csrf = client.get_cookie("csrf_access_token").value

    logout_response = client.post(
        "/api/v1/auth/logout", headers={"X-CSRF-TOKEN": csrf}
    )
    assert logout_response.status_code == 200
