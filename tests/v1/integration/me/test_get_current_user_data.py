from sqlalchemy import select

from domain.user.user_model import User
from schemas.me_schemas.me_responses import MeResponse
from tests.v1.integration.conftest import API_PREFIX, ME_ENDPOINT_PATH


def test_get_current_user_data_valid(client, logged_in_user, db_session):
    response = client.get(f"{API_PREFIX}{ME_ENDPOINT_PATH}/")
    assert response.status_code == 200

    user = db_session.scalar(select(User).where(User.id == logged_in_user.id))
    assert (
        MeResponse.from_model(user).model_dump(mode="json")
        == response.get_json()["data"]
    )


def test_get_current_user_data_csrf_absent(client, db_session):
    response = client.get(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/",
    )
    assert response.status_code == 401
