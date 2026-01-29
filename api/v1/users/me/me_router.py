from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from api.v1.responses import construct_error, construct_response
from di import me_service
from infrastructure.db import db_session
from infrastructure.jwt.jwt_utils import get_jwt_user_uuid
from schemas.admin_schemas.admin_users_schemas.admin_users_responses import (
    UserResponse,
)
from schemas.me_schemas.me_requests import (
    PasswordRequest,
    UpdateUserPersonalDataRequest,
)

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.patch("/update_password")
@jwt_required()
def update_password():
    try:
        data = PasswordRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

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
    try:
        data = UpdateUserPersonalDataRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

    with db_session() as session:
        user_id = get_jwt_user_uuid()
        user = me_service.update_personal_data(session, user_id, data)
        return construct_response(
            data=UserResponse.model_validate(user),
            message="User personal data was updated successfully",
        )


@bp.errorhandler(Exception)
def handle_exception(e: Exception):
    return construct_error(e)
