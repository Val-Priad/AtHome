import pytest
from sqlalchemy import select

from domain.user.user_model import User, UserRole
from exceptions.custom_exceptions.user_exceptions import UserNotFoundError
from tests.v1.integration.conftest import ADMIN_USERS_PATH, API_PREFIX


@pytest.mark.parametrize("logged_in_user", [UserRole.admin], indirect=True)
def test_delete_user_by_id_valid(logged_in_user, any_user, client, db_session):
    response = client.delete(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}",
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200

    with pytest.raises(UserNotFoundError):
        if not db_session.scalar(select(User).where(User.id == any_user.id)):
            raise UserNotFoundError


@pytest.mark.parametrize(
    "logged_in_user", [UserRole.user, UserRole.agent], indirect=True
)
def test_delete_user_by_id_forbidden(
    logged_in_user, any_user, client, db_session
):
    response = client.delete(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}",
        headers=logged_in_user.headers,
    )
    assert response.status_code == 403
    assert (
        db_session.scalar(select(User).where(User.id == any_user.id))
        is not None
    )
