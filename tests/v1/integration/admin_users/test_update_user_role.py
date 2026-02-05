import pytest
from sqlalchemy import select

from domain.user.user_model import User, UserRole
from tests.v1.integration.conftest import ADMIN_USERS_PATH, API_PREFIX


@pytest.mark.parametrize("logged_in_user", ["admin"], indirect=True)
def test_admin_can_promote_user_to_agent(
    logged_in_user, client, any_user, db_session
):
    response = client.patch(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}/role",
        json={"role": "agent"},
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200

    db_session.expire_all()
    user = db_session.scalar(select(User).where(User.id == any_user.id))
    assert user.role == UserRole.agent


@pytest.mark.parametrize("logged_in_user", ["admin"], indirect=True)
@pytest.mark.parametrize("any_user", ["agent"], indirect=True)
def test_admin_can_demote_agent_to_user(
    logged_in_user, client, any_user, db_session
):
    response = client.patch(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}/role",
        json={"role": "user"},
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200

    db_session.expire_all()
    user = db_session.scalar(select(User).where(User.id == any_user.id))
    assert user.role == UserRole.user


@pytest.mark.parametrize("logged_in_user", ["admin"], indirect=True)
@pytest.mark.parametrize("any_user", ["admin"], indirect=True)
def test_admin_cannot_demote_another_admin(
    logged_in_user, client, any_user, db_session
):
    response = client.patch(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}/role",
        json={"role": "user"},
        headers=logged_in_user.headers,
    )

    assert response.status_code == 403


@pytest.mark.parametrize("logged_in_user", ["admin"], indirect=True)
def test_admin_cannot_assign_invalid_role(logged_in_user, client, any_user):
    response = client.patch(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}/role",
        json={"role": "invalid_role"},
        headers=logged_in_user.headers,
    )
    assert response.status_code == 400
