from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from api.v1.responses import construct_error, construct_response
from di import me_service
from infrastructure.db import db_session
from infrastructure.jwt.jwt_utils import get_jwt_user_uuid
from schemas.me_schemas.me_requests import (
    PasswordRequest,
    UpdateUserPersonalDataRequest,
)
from schemas.me_schemas.me_responses import MeResponse

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.get("/")
@jwt_required()
def get_me():
    user_id = get_jwt_user_uuid()

    with db_session() as session:
        user = me_service.get_user_by_id(session, user_id)

        return construct_response(data=MeResponse.from_model(user))


@bp.delete("/")
@jwt_required()
def delete_me():
    user_id = get_jwt_user_uuid()

    with db_session() as session:
        me_service.delete_user_by_id(session, user_id)

    return construct_response()


@bp.patch("/update_password")
@jwt_required()
def update_password():
    data = PasswordRequest.from_request(request.json)

    with db_session() as session:
        user_id = get_jwt_user_uuid()

        me_service.verify_password(session, user_id, data.old_password)

        me_service.ensure_new_password_differs(
            data.old_password, data.new_password
        )

        me_service.update_password(session, user_id, data.new_password)
    return construct_response()


@bp.patch("/update-personal-data")
@jwt_required()
def update_personal_data():
    data = UpdateUserPersonalDataRequest.from_request(request.json)

    with db_session() as session:
        user_id = get_jwt_user_uuid()
        user = me_service.update_personal_data(session, user_id, data)
        return construct_response(
            data=MeResponse.from_model(user),
            message="User personal data was updated successfully",
        )


@bp.errorhandler(Exception)
def handle_exception(e: Exception):
    return construct_error(e)
