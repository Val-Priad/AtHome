from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from api.v1.responses import (
    construct_error,
    construct_no_content,
    construct_response,
)
from di import me_service
from infrastructure.db import db_session
from infrastructure.jwt.jwt_utils import get_jwt_user_uuid
from schemas.me_schemas import PasswordRequest, UpdateUserPersonalDataRequest

bp = Blueprint("users_me", __name__, url_prefix="/api/v1/users/me")


@bp.patch("/update_password")
@jwt_required()
def update_password():
    try:
        data = PasswordRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

    try:
        with db_session() as session:
            user_id = get_jwt_user_uuid()

            me_service.verify_password(session, user_id, data.old_password)

            me_service.ensure_new_password_differs(
                data.old_password, data.new_password
            )

            me_service.update_password(session, user_id, data.new_password)
    except Exception as e:
        current_app.logger.exception("Update password error")
        return construct_error(e)

    return construct_no_content()


@bp.patch("/update-personal-data")
@jwt_required()
def update_personal_data():
    try:
        data = UpdateUserPersonalDataRequest.model_validate(request.json)
    except ValidationError:
        return construct_error(code="validation_error")

    try:
        with db_session() as session:
            user_id = get_jwt_user_uuid()
            user = me_service.update_personal_data(session, user_id, data)
            user_data = user.to_dict()
    except Exception as e:
        current_app.logger.exception("Update personal data error")
        return construct_error(e)

    return construct_response(
        data=user_data,
        message="User personal data was updated successfully",
    )
