from sqlalchemy import select

from domain.user.user_model import User
from tests.v1.integration.conftest import API_PREFIX, ME_ENDPOINT_PATH


def test_delete_me_valid(client, logged_in_user, db_session):
    response = client.delete(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/", headers=logged_in_user.headers
    )
    assert response.status_code == 200
    assert (
        db_session.scalar(select(User).where(User.id == logged_in_user.id))
        is None
    )
